"""
This module provides tools for interacting with Google Calendar.

To use this module, you need to have a `credentials.json` file in the root
directory of the project. This file contains the Google Cloud credentials
for the application.

When the application is run for the first time, it will open a browser window
to authorize the application to access the user's Google Calendar. After
authorization, a `token.json` file will be created, which will be used for
subsequent requests.
"""

import datetime
import os.path
import os
import json
import pytz
import logging
import time
from typing import Optional, Dict, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tools.doctor_calendars import get_calendar_id_for_doctor

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/calendar.events"]

EDMONTON_TZ = pytz.timezone('America/Edmonton') # Define Edmonton timezone once

logger = logging.getLogger("dental-receptionist.calendar")

# Cache for service instance to avoid repeated token checks
_service_cache = None
_cache_timestamp = None
_cache_ttl = 300  # Cache for 5 minutes


class CalendarTokenError(Exception):
    """Custom exception for calendar token errors."""
    pass


def validate_calendar_credentials() -> Tuple[bool, Optional[str]]:
    """
    Validate if calendar credentials are available and valid.
    
    Supports multiple credential sources:
    1. Service account from GOOGLE_SERVICE_ACCOUNT_JSON env var
    2. OAuth token from GOOGLE_TOKEN_JSON env var
    3. token.json file (for local development)
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if credentials are valid, False otherwise
        - error_message: Error message if invalid, None if valid
    """
    creds = None
    
    # Check service account from environment (highest priority)
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        try:
            service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            logger.info("Validated service account credentials from environment")
            return True, None
        except Exception as e:
            error_msg = f"Error validating service account credentials: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Check OAuth token from environment
    elif os.getenv("GOOGLE_TOKEN_JSON"):
        try:
            token_data = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            
            if not creds:
                return False, "Failed to load credentials from GOOGLE_TOKEN_JSON"
            
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    # Try to refresh
                    try:
                        creds.refresh(Request())
                        logger.info("Successfully refreshed calendar token from environment")
                        return True, None
                    except RefreshError as e:
                        error_msg = (
                            f"Token refresh failed: {str(e)}. "
                            "The refresh token may have expired or been revoked. "
                            "Please update GOOGLE_TOKEN_JSON environment variable."
                        )
                        logger.error(error_msg)
                        return False, error_msg
                else:
                    return False, "Credentials from environment are invalid and cannot be refreshed."
            
            return True, None
        except Exception as e:
            error_msg = f"Error validating credentials from environment: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Fallback to file-based (local development)
    elif not os.path.exists("token.json"):
        return False, "No credentials found. Please set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_TOKEN_JSON environment variable, or authenticate with Google Calendar (token.json file)."
    
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds:
            return False, "Failed to load credentials from token.json"
        
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                # Try to refresh
                try:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open("token.json", "w") as token:
                        token.write(creds.to_json())
                    logger.info("Successfully refreshed calendar token")
                    return True, None
                except RefreshError as e:
                    error_msg = (
                        f"Token refresh failed: {str(e)}. "
                        "The refresh token may have expired or been revoked. "
                        "Please re-authenticate by deleting token.json and running the OAuth flow again."
                    )
                    logger.error(error_msg)
                    return False, error_msg
            else:
                return False, "Credentials are invalid and cannot be refreshed. Please re-authenticate."
        
        return True, None
        
    except Exception as e:
        error_msg = f"Error validating credentials: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def refresh_calendar_token() -> Tuple[bool, Optional[str]]:
    """
    Proactively refresh the calendar token.
    
    Returns:
        Tuple of (success, message)
        - success: True if refresh succeeded, False otherwise
        - message: Status message
    """
    if not os.path.exists("token.json"):
        return False, "token.json file not found. Please authenticate first."
    
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds:
            return False, "Failed to load credentials"
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                logger.info("Successfully refreshed calendar token proactively")
                return True, "Token refreshed successfully"
            except RefreshError as e:
                error_msg = (
                    f"Token refresh failed: {str(e)}. "
                    "The refresh token may have expired or been revoked. "
                    "To fix this:\n"
                    "1. Delete the token.json file\n"
                    "2. Run the OAuth flow again (this will open a browser for authentication)\n"
                    "3. The new token.json will be created automatically"
                )
                logger.error(error_msg)
                return False, error_msg
        elif creds.valid:
            return True, "Token is already valid, no refresh needed"
        else:
            return False, "Credentials cannot be refreshed. Please re-authenticate."
            
    except Exception as e:
        error_msg = f"Error refreshing token: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_calendar_service(retry_count: int = 3, retry_delay: float = 1.0):
    """
    Returns a Google Calendar service object with improved error handling.
    
    Args:
        retry_count: Number of retry attempts for token refresh
        retry_delay: Initial delay between retries (exponential backoff)
    
    Returns:
        Google Calendar service object
    
    Raises:
        CalendarTokenError: If token cannot be refreshed or OAuth flow cannot run
    """
    global _service_cache, _cache_timestamp
    
    # Check cache first
    if _service_cache and _cache_timestamp:
        elapsed = time.time() - _cache_timestamp
        if elapsed < _cache_ttl:
            return _service_cache
    
    creds = None
    
    # Priority 1: Try environment variables (for Vercel/serverless)
    using_service_account = False
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        try:
            service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            using_service_account = True
            logger.info("Loaded credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            # Service account credentials don't need validation/refresh - they're always valid
            # Build and return service immediately
            service = build('calendar', 'v3', credentials=creds)
            _service_cache = service
            _cache_timestamp = time.time()
            return service
        except Exception as e:
            logger.error(f"Error loading service account from environment: {e}")
            raise CalendarTokenError(
                f"Failed to load service account credentials from environment: {str(e)}"
            )
    
    # Priority 2: Try OAuth token from environment variables (for Vercel/serverless)
    elif os.getenv("GOOGLE_TOKEN_JSON") and os.getenv("GOOGLE_CREDENTIALS_JSON"):
        try:
            token_data = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            logger.info("Loaded credentials from GOOGLE_TOKEN_JSON environment variable")
        except Exception as e:
            logger.error(f"Error loading OAuth credentials from environment: {e}")
            raise CalendarTokenError(
                f"Failed to load OAuth credentials from environment: {str(e)}"
            )
    
    # Priority 3: Load credentials from token.json file (for local development)
    elif os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            logger.debug("Loaded credentials from token.json file")
        except Exception as e:
            logger.error(f"Error loading credentials from token.json: {e}")
            raise CalendarTokenError(
                f"Failed to load credentials: {str(e)}. "
                "Please check that token.json is valid or re-authenticate."
            )
    
    # If credentials are invalid or expired, try to refresh
    # Note: Service account credentials don't have .valid attribute and don't need refresh
    # Skip this check if we already handled service account above
    if not using_service_account and (not creds or not creds.valid):
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh with retry logic
            last_error = None
            for attempt in range(retry_count):
                try:
                    logger.info(f"Attempting to refresh token (attempt {attempt + 1}/{retry_count})")
                    creds.refresh(Request())
                    logger.info("Token refreshed successfully")
                    
                    # Save refreshed credentials (only if using file-based storage)
                    if not os.getenv("GOOGLE_TOKEN_JSON") and not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
                        try:
                            with open("token.json", "w") as token:
                                token.write(creds.to_json())
                            logger.debug("Saved refreshed credentials to token.json")
                        except Exception as e:
                            logger.warning(f"Failed to save refreshed credentials: {e}")
                    else:
                        logger.info("Token refreshed (using environment variables, not saving to file)")
                    
                    break  # Success, exit retry loop
                    
                except RefreshError as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Check if it's a permanent error (expired/revoked token)
                    if "invalid_grant" in error_str or "expired" in error_str or "revoked" in error_str:
                        error_msg = (
                            f"Token refresh failed: {str(e)}. "
                            "The refresh token has expired or been revoked. "
                            "OAuth flow cannot run automatically in server context. "
                            "To fix this:\n"
                            "1. Delete the token.json file\n"
                            "2. Run the OAuth flow manually (this requires user interaction):\n"
                            "   from tools.calendar_tools import get_calendar_service\n"
                            "   service = get_calendar_service()  # This will open browser\n"
                            "3. Or use a script that runs OAuth flow interactively"
                        )
                        logger.error(error_msg)
                        raise CalendarTokenError(error_msg)
                    
                    # For other errors, retry with exponential backoff
                    if attempt < retry_count - 1:
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(f"Token refresh failed, retrying in {delay}s: {e}")
                        time.sleep(delay)
                    else:
                        error_msg = (
                            f"Token refresh failed after {retry_count} attempts: {str(e)}. "
                            "Please check your network connection and try again, or re-authenticate."
                        )
                        logger.error(error_msg)
                        raise CalendarTokenError(error_msg)
                        
                except Exception as e:
                    error_msg = f"Unexpected error during token refresh: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    raise CalendarTokenError(error_msg)
        else:
            # No valid credentials and cannot refresh - need OAuth flow
            error_msg = (
                "No valid credentials found. OAuth flow cannot run automatically in server context. "
                "To fix this:\n"
                "1. Ensure credentials.json exists in the project root\n"
                "2. Run the OAuth flow manually (this requires user interaction):\n"
                "   from tools.calendar_tools import get_calendar_service\n"
                "   service = get_calendar_service()  # This will open browser\n"
                "3. Or use a script that runs OAuth flow interactively"
            )
            logger.error(error_msg)
            raise CalendarTokenError(error_msg)
    
    # Build and cache service
    try:
        service = build("calendar", "v3", credentials=creds)
        _service_cache = service
        _cache_timestamp = time.time()
        return service
    except Exception as e:
        error_msg = f"Failed to build calendar service: {str(e)}"
        logger.error(error_msg)
        raise CalendarTokenError(error_msg)


def view_available_slots(start_datetime: str, end_datetime: str, **kwargs):
    """
    Lists available appointment slots for a datetime range.
    
    Args:
        start_datetime: ISO datetime string (e.g., "2024-01-15T09:00:00" or "2024-01-15T09:00:00-07:00")
        end_datetime: ISO datetime string (e.g., "2024-01-16T17:00:00" or "2024-01-16T17:00:00-07:00")
        **kwargs: Additional keyword arguments including:
            - doctor_name: Optional doctor name to filter by specific doctor's calendar
    
    Returns:
        String describing available slots
    """
    try:
        service = get_calendar_service()
    except CalendarTokenError as e:
        return f"Calendar service unavailable: {str(e)}"

    # Parse datetime strings
    try:
        start_dt = datetime.datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
    except ValueError:
        return "Invalid datetime format. Please use ISO format (e.g., YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS-07:00)."

    # Convert to Edmonton timezone if not already timezone-aware
    if start_dt.tzinfo is None:
        start_dt_edmonton = EDMONTON_TZ.localize(start_dt)
    else:
        start_dt_edmonton = start_dt.astimezone(EDMONTON_TZ)
    
    if end_dt.tzinfo is None:
        end_dt_edmonton = EDMONTON_TZ.localize(end_dt)
    else:
        end_dt_edmonton = end_dt.astimezone(EDMONTON_TZ)

    # Get calendar ID based on doctor_name if provided
    doctor_name = kwargs.get('doctor_name')
    calendar_id = get_calendar_id_for_doctor(doctor_name)

    # Convert to UTC for Google Calendar API queries
    start_utc = start_dt_edmonton.astimezone(pytz.utc)
    end_utc = end_dt_edmonton.astimezone(pytz.utc)

    # Get all events for the given datetime range
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_utc.isoformat(),
                timeMax=end_utc.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                timeZone=str(EDMONTON_TZ)
            )
            .execute()
        )
        events = events_result.get("items", [])
    except HttpError as error:
        return f"An error occurred: {error}"

    # Generate all possible 1-hour slots in the datetime range
    possible_slots = []
    current_time_edmonton = start_dt_edmonton
    while current_time_edmonton < end_dt_edmonton:
        slot_end = min(current_time_edmonton + datetime.timedelta(hours=1), end_dt_edmonton)
        possible_slots.append((current_time_edmonton, slot_end))
        current_time_edmonton += datetime.timedelta(hours=1)

    # Find the busy slots in Edmonton timezone
    # Exclude cancelled and rescheduled events - they should not block availability
    busy_slots = []
    for event in events:
        # Skip cancelled events - they don't block availability
        event_status = event.get("status", "confirmed")
        event_summary = event.get("summary", "")
        
        # Skip if event is cancelled in Google Calendar
        if event_status == "cancelled":
            continue
        
        # Skip if event title indicates cancellation (our system marks cancelled appointments with [CANCELLED] prefix)
        if event_summary.startswith("[CANCELLED]"):
            continue
        
        # Skip if event title indicates rescheduling (our system marks rescheduled appointments with [RESCHEDULED] prefix)
        if event_summary.startswith("[RESCHEDULED]"):
            continue
        
        start_str = event["start"].get("dateTime", event["start"].get("date"))
        end_str = event["end"].get("dateTime", event["end"].get("date"))
        
        # Ensure event times are timezone-aware and convert to Edmonton timezone for comparison
        start_time_event = datetime.datetime.fromisoformat(start_str)
        end_time_event = datetime.datetime.fromisoformat(end_str)
        
        # Convert to Edmonton timezone if not already
        if start_time_event.tzinfo is None:
            start_time_event = EDMONTON_TZ.localize(start_time_event)
        else:
            start_time_event = start_time_event.astimezone(EDMONTON_TZ)

        if end_time_event.tzinfo is None:
            end_time_event = EDMONTON_TZ.localize(end_time_event)
        else:
            end_time_event = end_time_event.astimezone(EDMONTON_TZ)

        busy_slots.append((start_time_event, end_time_event))

    # Determine available slots
    available_slots = []
    for p_start, p_end in possible_slots:
        is_available = True
        for b_start, b_end in busy_slots:
            if max(p_start, b_start) < min(p_end, b_end):
                is_available = False
                break
        if is_available:
            # Format slot as date and time
            if p_start.date() == p_end.date():
                available_slots.append(f"{p_start.strftime('%Y-%m-%d')} {p_start.strftime('%H:%M')}")
            else:
                available_slots.append(f"{p_start.strftime('%Y-%m-%d %H:%M')} to {p_end.strftime('%Y-%m-%d %H:%M')}")

    if not available_slots:
        date_range_str = f"{start_dt_edmonton.strftime('%Y-%m-%d')} to {end_dt_edmonton.strftime('%Y-%m-%d')}"
        return f"No available slots from {date_range_str}."

    # Format response
    date_range_str = f"{start_dt_edmonton.strftime('%Y-%m-%d')} to {end_dt_edmonton.strftime('%Y-%m-%d')}"
    return f"Available slots from {date_range_str}: {', '.join(available_slots)}"


def create_new_event(
    start_time_str: str,
    end_time_str: str,
    appointment_id: str,
    patient_id: str,
    doctor_id: int,
    service_id: int,
    patient_name: str,
    service_name: str,
    reason: str,
    doctor_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Creates a new event in the Google Calendar with structured template.
    
    Args:
        start_time_str: ISO datetime string for start time
        end_time_str: ISO datetime string for end time
        appointment_id: UUID of the appointment
        patient_id: UUID of the patient
        doctor_id: ID of the doctor
        service_id: ID of the service
        patient_name: Full name of the patient
        service_name: Name of the service
        reason: Reason for visit
        doctor_name: Optional doctor name for calendar selection
    
    Returns:
        Dictionary with "event_id" and "html_link" keys
    
    Raises:
        CalendarTokenError: If calendar service is unavailable
        Exception: For other calendar operation errors
    """
    from tools.event_template import format_calendar_event
    
    try:
        service = get_calendar_service()
    except CalendarTokenError as e:
        logger.error(f"Failed to get calendar service for event creation: {e}")
        raise CalendarTokenError(f"Calendar service unavailable: {str(e)}")

    try:
        start_time_naive = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time_naive = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        
        # Make times timezone-aware in Edmonton timezone
        if start_time_naive.tzinfo is None:
            start_time_edmonton = EDMONTON_TZ.localize(start_time_naive)
        else:
            start_time_edmonton = start_time_naive.astimezone(EDMONTON_TZ)
        
        if end_time_naive.tzinfo is None:
            end_time_edmonton = EDMONTON_TZ.localize(end_time_naive)
        else:
            end_time_edmonton = end_time_naive.astimezone(EDMONTON_TZ)

    except ValueError:
        raise ValueError("Invalid datetime format. Please use ISO format (e.g., YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS-07:00).")

    # Format event using template
    event_data = format_calendar_event(
        appointment_id=appointment_id,
        patient_name=patient_name,
        service_name=service_name,
        patient_id=patient_id,
        doctor_id=doctor_id,
        service_id=service_id,
        reason=reason
    )

    # Get calendar ID based on doctor
    calendar_id = get_calendar_id_for_doctor(doctor_name)

    event = {
        "summary": event_data["summary"],
        "description": event_data["description"],
        "start": {
            "dateTime": start_time_edmonton.isoformat(),
            "timeZone": str(EDMONTON_TZ),
        },
        "end": {
            "dateTime": end_time_edmonton.isoformat(),
            "timeZone": str(EDMONTON_TZ),
        },
    }

    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return {
            "event_id": created_event.get('id'),
            "html_link": created_event.get('htmlLink', '')
        }
    except HttpError as error:
        raise Exception(f"Failed to create calendar event: {error}")
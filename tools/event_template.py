"""
Calendar event template formatting and parsing.

Provides structured format for calendar events that includes all necessary IDs
for database synchronization and easy retrieval.
"""

import re
from typing import Dict, Optional


def format_calendar_event(
    appointment_id: str,
    patient_name: str,
    service_name: str,
    patient_id: str,
    doctor_id: int,
    service_id: int,
    reason: str
) -> Dict[str, str]:
    """
    Format a calendar event with structured title and description.
    
    Args:
        appointment_id: UUID or ID of the appointment
        patient_name: Full name of the patient (e.g., "John Doe")
        service_name: Name of the service (e.g., "Routine Cleaning")
        patient_id: UUID or ID of the patient
        doctor_id: ID of the doctor
        service_id: ID of the service
        reason: Reason for visit/description
    
    Returns:
        Dictionary with "summary" (title) and "description" keys
    """
    # Parse patient name into first and last name
    name_parts = patient_name.strip().split(maxsplit=1)
    first_name = name_parts[0] if name_parts else "Unknown"
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Clean names for use in title
    def clean_name(text: str) -> str:
        """Clean name - keep only alphanumeric, remove special characters."""
        # Remove special characters, keep only alphanumeric and spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    def clean_service(text: str) -> str:
        """Clean service name - replace spaces and separators with hyphens."""
        # Replace spaces, underscores, and other separators with hyphens
        cleaned = re.sub(r'[\s_&()]+', '-', text)
        # Remove any remaining special characters except hyphens
        cleaned = re.sub(r'[^a-zA-Z0-9\-]', '', cleaned)
        # Remove multiple consecutive hyphens
        cleaned = re.sub(r'-+', '-', cleaned)
        # Remove leading/trailing hyphens
        cleaned = cleaned.strip('-')
        return cleaned
    
    first_name_clean = clean_name(first_name)
    last_name_clean = clean_name(last_name) if last_name else ""
    service_clean = clean_service(service_name)
    
    # Title format: APT_[First_name]-[Last_name]_[Service-with-hyphens]
    if last_name_clean:
        summary = f"APT_{first_name_clean}-{last_name_clean}_{service_clean}"
    else:
        summary = f"APT_{first_name_clean}_{service_clean}"
    
    # Description format: Structured, parseable KEY:VALUE pairs
    description = (
        f"APPOINTMENT_ID:{appointment_id}\n"
        f"PATIENT_ID:{patient_id}\n"
        f"DOCTOR_ID:{doctor_id}\n"
        f"SERVICE_ID:{service_id}\n"
        f"REASON:{reason}"
    )
    
    return {
        "summary": summary,
        "description": description
    }


def parse_calendar_event(description: str) -> Dict[str, Optional[str]]:
    """
    Parse a calendar event description to extract IDs.
    
    Args:
        description: Calendar event description string
    
    Returns:
        Dictionary with extracted IDs:
        {
            "appointment_id": "...",
            "patient_id": "...",
            "doctor_id": "...",
            "service_id": "...",
            "reason": "..."
        }
    """
    result = {
        "appointment_id": None,
        "patient_id": None,
        "doctor_id": None,
        "service_id": None,
        "reason": None
    }
    
    if not description:
        return result
    
    # Parse KEY:VALUE format
    # Match pattern: KEY:VALUE (where VALUE can contain any characters except newline)
    pattern = r"(\w+):(.+?)(?=\n\w+:|$)"
    matches = re.findall(pattern, description, re.MULTILINE)
    
    for key, value in matches:
        key_upper = key.upper()
        value_stripped = value.strip()
        
        if key_upper == "APPOINTMENT_ID":
            result["appointment_id"] = value_stripped
        elif key_upper == "PATIENT_ID":
            result["patient_id"] = value_stripped
        elif key_upper == "DOCTOR_ID":
            result["doctor_id"] = value_stripped
        elif key_upper == "SERVICE_ID":
            result["service_id"] = value_stripped
        elif key_upper == "REASON":
            result["reason"] = value_stripped
    
    return result


def parse_appointment_id_from_title(summary: str) -> Optional[str]:
    """
    Extract appointment ID from calendar event title.
    
    Note: New title format (APT_{FirstName}_{LastName}_{Service}) doesn't include appointment_id.
    Appointment ID should be retrieved from the event description instead.
    
    Args:
        summary: Calendar event title/summary
    
    Returns:
        None (appointment ID is not in title anymore, check description)
    """
    # New format doesn't include appointment_id in title
    # For backward compatibility, try to parse old format if it exists
    if not summary:
        return None
    
    # Try old format first (for backward compatibility)
    match = re.search(r'\[APT-([^\]]+)\]', summary)
    if match:
        return match.group(1)
    
    # New format doesn't have appointment_id in title
    return None

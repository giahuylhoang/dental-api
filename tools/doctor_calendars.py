"""
Doctor-to-Google Calendar ID mapping configuration.

Maps doctor names to their respective Google Calendar IDs.
Supports environment variable overrides for flexibility.
"""

import os
from typing import Optional

# Default calendar IDs (can be overridden via environment variables)
DOCTOR_CALENDARS = {
    "Dr. Johnson": "87368898113a2acdb1ddf6bdee677d86dd64a0340142d555f1d4fc6e289a461d@group.calendar.google.com",
    "Dr. Smith": "00ea57b212dfaf7a0b02cd2c40835cf8fd9bb0801298fa29da47251123fea8e9@group.calendar.google.com",
    "Dr. Ahmed": "a22e6e4e488a2f7848e5b1c8f1e49fbf439c732c4cae979ffdf05f2b86e53e78@group.calendar.google.com",
    # Default/fallback
    "default": "primary"  # Use primary calendar if no doctor specified
}


def get_calendar_id_for_doctor(doctor_name: Optional[str] = None) -> str:
    """
    Get the Google Calendar ID for a given doctor.
    
    Args:
        doctor_name: Name of the doctor (e.g., "Dr. Smith"). Case-insensitive.
                    If None or not found, returns "primary" calendar.
    
    Returns:
        Google Calendar ID string
    """
    if not doctor_name:
        return DOCTOR_CALENDARS.get("default", "primary")
    
    # Check environment variables first (for overrides)
    env_key = doctor_name.upper().replace(" ", "_").replace(".", "").replace("-", "_")
    env_calendar_id = os.getenv(f"DOCTOR_{env_key}_CALENDAR_ID")
    if env_calendar_id:
        return env_calendar_id
    
    # Case-insensitive lookup in default mapping
    doctor_name_normalized = doctor_name.strip()
    for key, calendar_id in DOCTOR_CALENDARS.items():
        if key.lower() == doctor_name_normalized.lower():
            return calendar_id
    
    # Fallback to primary if not found
    return DOCTOR_CALENDARS.get("default", "primary")

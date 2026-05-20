"""Slot-availability service — thin wrapper around tools.slot_utils.

Exists so routers can import from services/ instead of reaching directly
into tools/. No behavioral change vs. calling
tools.slot_utils.get_available_slots directly.
"""
from typing import Dict, Optional

from sqlalchemy.orm import Session

from tools.slot_utils import get_available_slots as _underlying


def get_available_slots(
    db: Session,
    start_datetime: str,
    end_datetime: str,
    provider_id: Optional[int] = None,
    provider_name: Optional[str] = None,
    slot_minutes: int = 30,
    clinic_id: Optional[str] = None,
    timezone_str: Optional[str] = None,
    hour_start: Optional[int] = None,
    hour_end: Optional[int] = None,
) -> Dict[str, object]:
    """Compute available appointment slots from the database.

    Delegates to tools.slot_utils.get_available_slots. Signature matches the
    underlying function 1:1 — do not add or remove parameters here.
    """
    return _underlying(
        db,
        start_datetime,
        end_datetime,
        provider_id=provider_id,
        provider_name=provider_name,
        slot_minutes=slot_minutes,
        clinic_id=clinic_id,
        timezone_str=timezone_str,
        hour_start=hour_start,
        hour_end=hour_end,
    )


__all__ = ["get_available_slots"]

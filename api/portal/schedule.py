"""GET /api/portal/clinics/{cid}/schedule — read-only proxy to v1 slot service.

Reuses services.slots.get_available_slots so the portal sees the same slots
as the agent (no HTTP hop, in-process call).
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from services.slots import get_available_slots

router = APIRouter()


@router.get("")
def get_schedule(
    clinic_id: str,
    start: str = Query(..., description="ISO datetime or date — start of range"),
    end: str = Query(..., description="ISO datetime or date — end of range"),
    provider_id: int | None = Query(None),
    slot_minutes: int = Query(30, ge=5, le=240),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return get_available_slots(
        db=db,
        start_datetime=start,
        end_datetime=end,
        provider_id=provider_id,
        slot_minutes=slot_minutes,
        clinic_id=clinic_id,
    )

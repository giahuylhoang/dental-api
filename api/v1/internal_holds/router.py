"""POST /api/internal/holds — voice-channel intake.

Thin sibling of api/v1/public_holds/router.py, sharing the same
create_hold service.  Differences:
  - Path prefix: /api/internal (NOT /api/public — never BFF-proxied)
  - Auth: require_internal_secret (enforced even under ADMIN_AUTH_BYPASS)
  - source: hard-coded to "voice-hold"; not in the request body
  - No reCAPTCHA / insurance fields (not relevant for voice channel)
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import require_internal_secret
from database.connection import get_db
from database.models import Clinic, Provider
from services.holds import create_hold
from services.tz_utils import to_storage_utc_clinic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/internal", tags=["internal-holds"])


# ---------------------------------------------------------------------------
# Schemas (no reCAPTCHA, no insurance — voice channel only)
# ---------------------------------------------------------------------------


class InternalHoldRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    new_patient: bool
    provider_id: int
    service_id: Optional[int] = None
    service_name: str = "Consultation"
    start_time: str
    end_time: str
    message: Optional[str] = None


class InternalHoldResponse(BaseModel):
    appointment_id: str
    status: str
    provider_id: int
    start_time: str
    end_time: str
    source: str


# ---------------------------------------------------------------------------
# Helpers (mirror public_holds._resolve_clinic)
# ---------------------------------------------------------------------------


def _resolve_clinic(db: Session, clinic_id: str) -> Clinic:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if clinic is None:
        raise HTTPException(status_code=404, detail="clinic_not_found")
    return clinic


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/holds", response_model=InternalHoldResponse)
def create_internal_hold(
    payload: InternalHoldRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_secret),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    """Create a PENDING voice-hold.

    source is hard-coded to "voice-hold" — the caller (Emma) cannot forge a
    different channel value because this endpoint is not exposed via the BFF.
    """
    clinic = _resolve_clinic(db, x_clinic_id)
    start = to_storage_utc_clinic(datetime.fromisoformat(payload.start_time), clinic)
    end = to_storage_utc_clinic(datetime.fromisoformat(payload.end_time), clinic)
    created_at_utc = datetime.utcnow()

    # provider_id is required for voice-holds (Emma always resolves a specific
    # provider before booking).
    candidate_ids = [payload.provider_id]

    reason = (payload.message or "").strip()
    tags = [f"{'New' if payload.new_patient else 'Existing'} patient"]
    reason_note = " | ".join(tags) + (f" | {reason}" if reason else "")

    last_exc = None
    for pid in candidate_ids:
        try:
            appt = create_hold(
                db, background_tasks, clinic=clinic, provider_id=pid,
                service_id=payload.service_id, service_name=payload.service_name,
                name=payload.name, phone=payload.phone, email=payload.email,
                start=start, end=end, reason=reason_note,
                source="voice-hold",
                created_at_utc=created_at_utc,
            )
            db.commit()
            db.refresh(appt)
            return InternalHoldResponse(
                appointment_id=appt.id,
                status=appt.status.value,
                provider_id=appt.provider_id,
                start_time=payload.start_time,
                end_time=payload.end_time,
                source=appt.source,
            )
        except HTTPException as e:
            db.rollback()
            if e.status_code == 409:
                last_exc = e
                continue
            raise
    raise last_exc or HTTPException(status_code=409, detail="slot_unavailable")

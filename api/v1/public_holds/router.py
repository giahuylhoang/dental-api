import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Clinic, Provider
from api.dependencies.auth import get_internal_caller
from services.holds import create_hold
from services.tz_utils import to_storage_utc
from .schemas import PublicHoldRequest, PublicHoldResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public-holds"])


def _resolve_clinic(db: Session, clinic_id: str) -> Clinic:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if clinic is None:
        raise HTTPException(status_code=404, detail="clinic_not_found")
    return clinic


@router.post("/holds", response_model=PublicHoldResponse)
def create_public_hold(
    payload: PublicHoldRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(get_internal_caller),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    clinic = _resolve_clinic(db, x_clinic_id)
    start = to_storage_utc(datetime.fromisoformat(payload.start_time))
    end = to_storage_utc(datetime.fromisoformat(payload.end_time))
    created_at_utc = datetime.utcnow()

    candidate_ids = [payload.provider_id] if payload.provider_id else [
        p.id for p in db.query(Provider).filter(
            Provider.clinic_id == clinic.id,
            Provider.is_active.is_(True),
        ).all()
    ]
    if not candidate_ids:
        raise HTTPException(status_code=400, detail="no_provider_available")

    reason = (payload.message or "").strip()
    tags = [f"{'New' if payload.new_patient else 'Existing'} patient"]
    if payload.insurance:
        ins = payload.insurance
        if payload.insurance == "Other" and payload.insurance_other:
            ins = f"Other: {payload.insurance_other}"
        tags.append(f"Insurance: {ins}")
    reason_note = " | ".join(tags) + (f" | {reason}" if reason else "")

    last_exc = None
    for pid in candidate_ids:
        try:
            appt = create_hold(
                db, background_tasks, clinic=clinic, provider_id=pid,
                service_id=payload.service_id, service_name=payload.service_name,
                name=payload.name, phone=payload.phone, email=payload.email,
                start=start, end=end, reason=reason_note, source=payload.source,
                created_at_utc=created_at_utc,
            )
            db.commit()
            db.refresh(appt)
            return PublicHoldResponse(
                appointment_id=appt.id,
                status=appt.status.value,
                provider_id=appt.provider_id,
                start_time=payload.start_time,
                end_time=payload.end_time,
            )
        except HTTPException as e:
            db.rollback()
            if e.status_code == 409:
                last_exc = e
                continue
            raise
    raise last_exc or HTTPException(status_code=409, detail="slot_unavailable")

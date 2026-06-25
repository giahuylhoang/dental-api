import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Clinic, Provider, Appointment
from api.dependencies.auth import require_internal_secret
from services.holds import create_hold
from services.hold_tokens import verify_confirm_token
from services.slots import get_available_slots
from services.tz_utils import to_storage_utc_clinic
from .schemas import PublicHoldRequest, PublicHoldResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public-holds"])


def _resolve_clinic(db: Session, clinic_id: str) -> Clinic:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if clinic is None:
        raise HTTPException(status_code=404, detail="clinic_not_found")
    return clinic


@router.get("/slots")
def get_public_slots(
    start_datetime: str = Query(..., description="ISO datetime string"),
    end_datetime: str = Query(..., description="ISO datetime string"),
    provider_id: Optional[int] = Query(None, description="Provider ID for filtering"),
    provider_name: Optional[str] = Query(None, description="Provider name for filtering"),
    slot_minutes: int = Query(30, description="Slot duration in minutes"),
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_secret),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    """Get available appointment slots (internal-secret gated).

    Identical payload to GET /api/calendar/slots, but authenticates via
    X-Internal-Secret + X-Clinic-Id instead of Firebase, so the booking BFF
    can call it without a Firebase user token.
    """
    clinic = _resolve_clinic(db, x_clinic_id)
    try:
        slots = get_available_slots(
            db=db,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            provider_id=provider_id,
            provider_name=provider_name,
            slot_minutes=slot_minutes,
            clinic_id=clinic.id,
            timezone_str=clinic.timezone,
            hour_start=clinic.working_hour_start,
            hour_end=clinic.working_hour_end,
        )
        return slots
    except Exception as e:
        logger.error(f"Error in get_public_slots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/holds", response_model=PublicHoldResponse)
def create_public_hold(
    payload: PublicHoldRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_secret),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    clinic = _resolve_clinic(db, x_clinic_id)
    start = to_storage_utc_clinic(datetime.fromisoformat(payload.start_time), clinic)
    end = to_storage_utc_clinic(datetime.fromisoformat(payload.end_time), clinic)
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
                dob=payload.dob,
                start=start, end=end, reason=reason_note, source="booking-web-hold",
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


@router.post("/holds/confirm")
def patient_self_confirm(
    token: str,
    db: Session = Depends(get_db),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    appointment_id = verify_confirm_token(token)
    if not appointment_id:
        raise HTTPException(status_code=400, detail="invalid_token")
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.clinic_id == x_clinic_id)
        .first()
    )
    if appt is None:
        raise HTTPException(status_code=404, detail="hold_not_found")
    appt.patient_confirmed = True
    db.commit()
    return {"appointment_id": appt.id, "patient_confirmed": True}

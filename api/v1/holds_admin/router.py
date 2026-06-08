"""Staff-facing holds admin routes — list, confirm, and decline pending holds."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from api.dependencies import get_authorized_clinic, get_db
from database.models import Clinic, Appointment, AppointmentStatus
from services.holds import confirm_hold, decline_hold

router = APIRouter(prefix="/api/holds", tags=["holds-admin"])


def _get_hold(db: Session, clinic: Clinic, appt_id: str) -> Appointment:
    appt = (
        db.query(Appointment)
        .filter(
            Appointment.id == appt_id,
            Appointment.clinic_id == clinic.id,
            Appointment.status == AppointmentStatus.PENDING,
        )
        .first()
    )
    if appt is None:
        raise HTTPException(status_code=404, detail="hold_not_found")
    return appt


@router.get("/pending")
def list_pending_holds(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """List all PENDING holds (hold_expiry_at not null) for the clinic, oldest first."""
    rows = (
        db.query(Appointment)
        .filter(
            Appointment.clinic_id == clinic.id,
            Appointment.status == AppointmentStatus.PENDING,
            Appointment.hold_expiry_at.isnot(None),
        )
        .order_by(Appointment.created_at.asc())
        .all()
    )
    out = []
    for a in rows:
        out.append({
            "appointment_id": a.id,
            "source": a.source,
            "provider_id": a.provider_id,
            "provider_name": a.provider.name if a.provider else None,
            "patient_name": (
                f"{a.patient.first_name} {a.patient.last_name}".strip()
                if a.patient else None
            ),
            "patient_phone": a.patient.phone if a.patient else None,
            "start_time": a.start_time.isoformat(),
            "end_time": a.end_time.isoformat(),
            "patient_confirmed": a.patient_confirmed,
            "reason_note": a.reason_note,
            "hold_expiry_at": a.hold_expiry_at.isoformat() if a.hold_expiry_at else None,
        })
    return out


@router.post("/{appt_id}/confirm")
def confirm(
    appt_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Confirm a pending hold: PENDING -> SCHEDULED, fires source-aware SMS."""
    appt = _get_hold(db, clinic, appt_id)
    confirm_hold(
        db,
        background_tasks,
        clinic=clinic,
        appointment=appt,
        service_name=appt.service.name if appt.service else "Consultation",
    )
    db.commit()
    return {"appointment_id": appt.id, "status": appt.status.value}


@router.post("/{appt_id}/decline")
def decline(
    appt_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Decline a pending hold: PENDING -> CANCELLED, frees the slot."""
    appt = _get_hold(db, clinic, appt_id)
    decline_hold(db, clinic=clinic, appointment=appt)
    db.commit()
    return {"appointment_id": appt.id, "status": appt.status.value}

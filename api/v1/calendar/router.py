"""v1 calendar router — /api/calendar/slots and /api/calendar/events.

POST /api/calendar/events is the canonical booking endpoint. POST
/api/appointments aliases it (see api/v1/appointments/router.py).
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import (
    Appointment, AppointmentStatus, Clinic, Patient, Provider, Service,
)
from api.v1.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentResponse,
)
from services.appointments import check_conflicts_for_create
from services.notifications import schedule_booking_notifications
from services.slots import get_available_slots

logger = logging.getLogger("dental-receptionist")

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/slots")
async def get_calendar_slots(
    start_datetime: str = Query(..., description="ISO datetime string"),
    end_datetime: str = Query(..., description="ISO datetime string"),
    provider_id: Optional[int] = Query(None, description="Provider ID for filtering"),
    provider_name: Optional[str] = Query(None, description="Provider name for filtering"),
    slot_minutes: int = Query(30, description="Slot duration in minutes"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Get available appointment slots for a datetime range (computed from database).
    Per-clinic working hours and timezone from X-Clinic-Id.
    """
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
        logger.error(f"Error in get_calendar_slots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def list_calendar_events(
    start: Optional[str] = Query(None, description="ISO start of range (inclusive)"),
    end: Optional[str] = Query(None, description="ISO end of range (exclusive)"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List appointments in [start, end) as FullCalendar-style event objects."""
    q = db.query(Appointment).filter(Appointment.clinic_id == clinic.id)
    if start:
        try:
            q = q.filter(Appointment.start_time >= datetime.fromisoformat(start.replace("Z", "+00:00")))
        except ValueError:
            raise HTTPException(400, f"Invalid start datetime: {start}")
    if end:
        try:
            q = q.filter(Appointment.start_time < datetime.fromisoformat(end.replace("Z", "+00:00")))
        except ValueError:
            raise HTTPException(400, f"Invalid end datetime: {end}")
    out = []
    for appt in q.order_by(Appointment.start_time.asc()).all():
        out.append({
            "id": appt.id,
            "title": (appt.notes or "Appointment")[:60],
            "start": appt.start_time.isoformat() if appt.start_time else None,
            "end": appt.end_time.isoformat() if appt.end_time else None,
            "status": appt.status.value if hasattr(appt.status, "value") else str(appt.status),
            "patient_id": appt.patient_id,
            "provider_id": appt.provider_id,
        })
    return out


@router.post("/events")
async def create_calendar_event(
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create appointment in database (DB is source of truth)."""
    # 0. Validate datetime formats BEFORE creating appointment
    try:
        start_time_dt = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid start_time format: {str(e)}. Expected ISO datetime format."
        )

    try:
        end_time_dt = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid end_time format: {str(e)}. Expected ISO datetime format."
        )

    # Validate end_time is after start_time
    if end_time_dt <= start_time_dt:
        raise HTTPException(
            status_code=400,
            detail="end_time must be after start_time"
        )

    # Validate patient_id exists and belongs to clinic
    patient = db.query(Patient).filter(Patient.id == request.patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate provider_id exists and belongs to clinic
    provider = db.query(Provider).filter(
        Provider.id == request.provider_id, Provider.clinic_id == clinic.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Validate service_id exists and belongs to clinic (if provided)
    if request.service_id is not None:
        service = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

    # Reject conflicts with active appointments or recurring busy blocks.
    # Slot listing already hides these — this guard closes the loop for direct
    # API calls / stale UI tabs.
    check_conflicts_for_create(
        db,
        clinic=clinic,
        provider_id=request.provider_id,
        start=start_time_dt,
        end=end_time_dt,
    )

    # 1. Create appointment in database — normalize to naive UTC so SQLite
    #    and Postgres store the same value regardless of input offset.
    from services.tz_utils import to_storage_utc
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=request.patient_id,
        provider_id=request.provider_id,
        service_id=request.service_id,
        start_time=to_storage_utc(start_time_dt),
        end_time=to_storage_utc(end_time_dt),
        reason_note=request.reason,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Resolve service name for notifications + SSE (DB lookup beats request fallback)
    svc = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first() if request.service_id else None
    service_name = (svc.name if svc else None) or request.service_name

    # Schedule patient SMS + clinic email (best-effort, failures logged in the service)
    schedule_booking_notifications(
        background_tasks,
        patient=patient,
        provider=provider,
        appointment=appointment,
        clinic=clinic,
        service_name=service_name,
    )

    # SSE: notify any subscribed CRM clients (in-process; no-op if no
    # subscribers). Wrapped in try/except so a bus failure can NEVER
    # poison the booking response — the appointment is already committed
    # by this point.
    provider_display_name = " ".join(filter(None, [provider.title, provider.name])).strip() or provider.name
    patient_name = " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"
    from services.tz_utils import format_clinic_local, to_clinic_local_iso
    date_str, time_str = format_clinic_local(appointment.start_time, clinic)
    try:
        from api.v2.events import publish_appointment_created
        publish_appointment_created(clinic.id, {
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "patient_name": patient_name,
            "provider_id": appointment.provider_id,
            "provider_name": provider_display_name,
            "service_id": appointment.service_id,
            "service_name": service_name,
            "start_time": to_clinic_local_iso(appointment.start_time, clinic),
            "end_time": to_clinic_local_iso(appointment.end_time, clinic),
            "start_time_local": f"{date_str} {time_str}",
            "status": appointment.status.value,
        })
    except Exception as e:
        logger.warning("SSE publish_appointment_created failed: %s", e)

    return AppointmentResponse(
        appointment_id=appointment.id,
        calendar_event_id=None,
        calendar_link=None,
        status=appointment.status.value,
    )

"""v1 appointments router — /api/appointments and nested actions."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from api.dependencies import get_clinic, get_db
from api.serializers import _to_appointment_detail
from database.models import (
    Appointment, AppointmentStatus, Clinic, Patient, Provider, Service,
)

from api.v1.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentDetailResponse,
    AppointmentResponse,
    AppointmentStatusUpdateRequest,
)
from services.appointments import check_conflicts_for_reschedule
from services.notifications import (
    schedule_cancellation_notification,
    schedule_reschedule_notification,
)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("", response_model=List[AppointmentDetailResponse])
async def list_appointments(
    appointment_id: Optional[str] = Query(None, description="Filter by specific appointment ID"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    provider_id: Optional[int] = Query(None, description="Filter by provider ID"),
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, CANCELLED, COMPLETED, NO_SHOW, PENDING)"),
    start_date: Optional[str] = Query(None, description="Filter appointments starting from this date (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter appointments ending before this date (ISO format: YYYY-MM-DD)"),
    start_datetime: Optional[str] = Query(None, description="Filter appointments starting from this datetime (ISO format)"),
    end_datetime: Optional[str] = Query(None, description="Filter appointments ending before this datetime (ISO format)"),
    date: Optional[str] = Query(None, description="Filter appointments on a specific date (ISO format: YYYY-MM-DD)"),
    provider_name: Optional[str] = Query(None, description="Filter by provider name"),
    patient_name: Optional[str] = Query(None, description="Filter by patient name (searches first_name and last_name)"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    List appointments with comprehensive filtering options.

    Supports filtering by:
    - appointment_id: Get specific appointment
    - patient_id: All appointments for a patient
    - provider_id: All appointments for a provider
    - service_id: All appointments for a service
    - status: Filter by appointment status
    - start_date/end_date: Date range filtering
    - start_datetime/end_datetime: Datetime range filtering
    - date: Appointments on a specific date
    - provider_name: Filter by provider name
    - patient_name: Filter by patient name (partial match)
    """
    query = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic.id)
        .options(joinedload(Appointment.provider), joinedload(Appointment.service))
    )

    # Filter by appointment ID (returns single result if found)
    if appointment_id:
        query = query.filter(Appointment.id == appointment_id)

    # Filter by patient ID
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)

    # Filter by provider ID
    if provider_id:
        query = query.filter(Appointment.provider_id == provider_id)

    # Filter by service ID
    if service_id:
        query = query.filter(Appointment.service_id == service_id)

    # Filter by status
    if status:
        try:
            status_enum = AppointmentStatus(status.upper())
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid values: SCHEDULED, CANCELLED, COMPLETED, NO_SHOW, PENDING")

    # Filter by provider name (scoped to clinic)
    if provider_name:
        provider = db.query(Provider).filter(
            Provider.clinic_id == clinic.id, Provider.name.ilike(f"%{provider_name}%")
        ).first()
        if provider:
            query = query.filter(Appointment.provider_id == provider.id)
        else:
            # Return empty list if provider not found
            return []

    # Filter by patient name (scoped to clinic)
    if patient_name:
        patients = db.query(Patient).filter(
            Patient.clinic_id == clinic.id,
            (Patient.first_name.ilike(f"%{patient_name}%")) |
            (Patient.last_name.ilike(f"%{patient_name}%"))
        ).all()
        if patients:
            patient_ids = [p.id for p in patients]
            query = query.filter(Appointment.patient_id.in_(patient_ids))
        else:
            # Return empty list if no patients found
            return []

    # Date range filtering
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Appointment.start_time >= datetime.combine(start_dt, datetime.min.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Appointment.end_time <= datetime.combine(end_dt, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    # Datetime range filtering (more precise)
    if start_datetime:
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            query = query.filter(Appointment.start_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_datetime format. Use ISO format")

    if end_datetime:
        try:
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            query = query.filter(Appointment.end_time <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_datetime format. Use ISO format")

    # Filter by specific date
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            query = query.filter(
                Appointment.start_time >= start_of_day,
                Appointment.start_time <= end_of_day
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    appointments = query.order_by(Appointment.start_time).all()
    return [_to_appointment_detail(apt, clinic) for apt in appointments]


@router.delete("/bulk/date/{date}")
async def delete_appointments_by_date_endpoint(
    date: str,
    dry_run: bool = Query(False, description="If true, only preview without deleting"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Delete all appointments for a specific date from database.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2025-12-22")
        dry_run: If true, only return what would be deleted without actually deleting
    """
    import pytz

    try:
        target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-22)",
        )

    tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    start_of_day = tz.localize(datetime.combine(target_date_obj, datetime.min.time()))
    end_of_day = tz.localize(datetime.combine(target_date_obj, datetime.max.time()))

    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.start_time >= start_of_day,
        Appointment.start_time <= end_of_day,
    ).all()

    if not appointments:
        return {
            "message": f"No appointments found for {date}",
            "date": date,
            "appointments_found": 0,
            "deleted": 0,
        }

    if dry_run:
        return {
            "message": f"DRY RUN: Would delete {len(appointments)} appointment(s) for {date}",
            "date": date,
            "appointments_found": len(appointments),
            "appointments": [
                {
                    "id": apt.id,
                    "patient_id": apt.patient_id,
                    "provider_id": apt.provider_id,
                    "start_time": apt.start_time.isoformat(),
                    "status": apt.status.value,
                }
                for apt in appointments
            ],
            "deleted": 0,
        }

    import logging
    _logger = logging.getLogger("dental-receptionist")

    deleted_count = 0
    failed_count = 0
    deleted_ids = []
    failed_ids = []

    for appointment in appointments:
        appointment_id = appointment.id
        try:
            db.delete(appointment)
            db.commit()
            deleted_count += 1
            deleted_ids.append(appointment_id)
        except Exception as e:
            db.rollback()
            failed_count += 1
            failed_ids.append(appointment_id)
            _logger.warning(f"Failed to delete appointment {appointment_id}: {e}")

    return {
        "message": f"Deleted {deleted_count} appointment(s) for {date}",
        "date": date,
        "appointments_found": len(appointments),
        "deleted": deleted_count,
        "failed": failed_count,
        "deleted_ids": deleted_ids,
        "failed_ids": failed_ids,
    }


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
async def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get appointment by ID."""
    appointment = (
        db.query(Appointment)
        .options(joinedload(Appointment.provider), joinedload(Appointment.service))
        .filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _to_appointment_detail(appointment, clinic)


@router.post("", response_model=AppointmentResponse)
async def create_appointment(
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create appointment (also creates calendar event)."""
    # Lazy import: Task 11 will move create_calendar_event into the v1 calendar
    # router; until then it still lives in api.main. After Task 11 the import
    # path becomes api.v1.calendar.router.
    try:
        from api.v1.calendar.router import create_calendar_event
    except ImportError:
        from api.main import create_calendar_event  # type: ignore
    return await create_calendar_event(request, background_tasks, db, clinic)


@router.put("/{appointment_id}", response_model=AppointmentDetailResponse)
async def update_appointment(
    appointment_id: str,
    updates: dict,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update appointment in database."""
    appointment = (
        db.query(Appointment)
        .options(joinedload(Appointment.provider), joinedload(Appointment.service))
        .filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    from services.tz_utils import to_storage_utc
    for key, value in updates.items():
        if hasattr(appointment, key):
            if key in ["start_time", "end_time"]:
                setattr(
                    appointment,
                    key,
                    to_storage_utc(datetime.fromisoformat(value.replace("Z", "+00:00"))),
                )
            else:
                setattr(appointment, key, value)

    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)
    return _to_appointment_detail(appointment, clinic)


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Delete appointment permanently from database.
    Use PUT /api/appointments/{id}/cancel if you want to cancel but keep the record.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    try:
        db.delete(appointment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete appointment from database: {str(e)}",
        )

    return {
        "message": "Appointment deleted successfully",
        "appointment_id": appointment_id,
    }


@router.put("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Cancel appointment (marks as CANCELLED but keeps record).
    Use DELETE endpoint if you want to permanently remove the appointment.
    """
    appointment = (
        db.query(Appointment)
        .options(joinedload(Appointment.provider), joinedload(Appointment.service))
        .filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    # Schedule cancellation SMS (best-effort; failures are logged in the service)
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id, Patient.clinic_id == clinic.id).first()
    provider = db.query(Provider).filter(Provider.id == appointment.provider_id, Provider.clinic_id == clinic.id).first()
    if patient and provider:
        schedule_cancellation_notification(
            background_tasks,
            patient=patient,
            provider=provider,
            appointment=appointment,
            clinic=clinic,
        )

    return _to_appointment_detail(appointment, clinic)


@router.put("/{appointment_id}/status", response_model=AppointmentDetailResponse)
async def update_appointment_status(
    appointment_id: str,
    request: AppointmentStatusUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update appointment status in database."""
    try:
        new_status = AppointmentStatus(request.status.upper())
    except ValueError:
        valid_statuses = [s.value for s in AppointmentStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Valid values: {', '.join(valid_statuses)}",
        )

    appointment = (
        db.query(Appointment)
        .options(joinedload(Appointment.provider), joinedload(Appointment.service))
        .filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = new_status
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    return _to_appointment_detail(appointment, clinic)


@router.put("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Reschedule an existing appointment.
    Creates a new appointment with the new time/date and marks the old one as RESCHEDULED.
    """
    old_appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not old_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if old_appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reschedule appointment with status {old_appointment.status.value}. Only SCHEDULED appointments can be rescheduled.",
        )

    try:
        new_start_time = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        new_end_time = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))

        check_conflicts_for_reschedule(
            db,
            clinic=clinic,
            provider_id=request.provider_id,
            start=new_start_time,
            end=new_end_time,
            excluding_appointment_id=appointment_id,
        )

        from services.tz_utils import to_storage_utc
        new_appointment = Appointment(
            clinic_id=clinic.id,
            patient_id=request.patient_id,
            provider_id=request.provider_id,
            service_id=request.service_id,
            start_time=to_storage_utc(new_start_time),
            end_time=to_storage_utc(new_end_time),
            reason_note=request.reason,
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(new_appointment)
        db.flush()

        old_appointment.status = AppointmentStatus.RESCHEDULED
        old_appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(new_appointment)
        db.refresh(old_appointment)

        # Schedule reschedule confirmation SMS (best-effort)
        patient = db.query(Patient).filter(Patient.id == request.patient_id, Patient.clinic_id == clinic.id).first()
        provider = db.query(Provider).filter(Provider.id == request.provider_id, Provider.clinic_id == clinic.id).first()
        svc = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first() if request.service_id else None
        service_name = (svc.name if svc else None) or request.service_name
        if patient and provider:
            schedule_reschedule_notification(
                background_tasks,
                patient=patient,
                provider=provider,
                new_start_time=new_start_time,
                clinic=clinic,
                service_name=service_name,
            )

        return {
            "old_appointment_id": old_appointment.id,
            "new_appointment_id": new_appointment.id,
            "status": "RESCHEDULED",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger("dental-receptionist").error(f"Error rescheduling appointment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error rescheduling appointment: {str(e)}")

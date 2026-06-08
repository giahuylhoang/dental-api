import uuid
from datetime import datetime, timedelta, time as dtime
import pytz
from sqlalchemy.orm import Session
from database.models import Appointment, AppointmentStatus, Clinic, Patient
from database.v1_1.models import ClinicOperatingHours, ClinicHoliday


def _open_hours_for(db: Session, clinic_id: str, dow: int):
    """Return (open_at, close_at) if the clinic is open that weekday, else None.
    Falls back to Mon-Fri 9->17 when no per-day rows exist."""
    row = (
        db.query(ClinicOperatingHours)
        .filter(ClinicOperatingHours.clinic_id == clinic_id,
                ClinicOperatingHours.day_of_week == dow)
        .first()
    )
    if row is not None:
        if row.is_closed:
            return None
        return row.open_at, row.close_at
    if dow >= 5:
        return None
    return dtime(9, 0), dtime(17, 0)


def compute_hold_expiry(db: Session, clinic: Clinic, created_at_utc: datetime) -> datetime:
    """Expire at clinic close of the next open business day after creation day.
    `created_at_utc` is naive UTC; returns naive UTC."""
    tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    local_created = pytz.utc.localize(created_at_utc).astimezone(tz)
    day = local_created.date()
    for _ in range(1, 30):
        day = day + timedelta(days=1)
        hours = _open_hours_for(db, clinic.id, day.weekday())
        if hours is None:
            continue
        is_holiday = (
            db.query(ClinicHoliday)
            .filter(ClinicHoliday.clinic_id == clinic.id,
                    ClinicHoliday.holiday_date == day)
            .first()
            is not None
        )
        if is_holiday:
            continue
        _open_at, close_at = hours
        expiry_local = tz.localize(datetime.combine(day, close_at))
        return expiry_local.astimezone(pytz.utc).replace(tzinfo=None)
    raise RuntimeError(f"No open business day found within 30 days for clinic {clinic.id}")


def create_hold(
    db: Session,
    background_tasks,
    *,
    clinic: Clinic,
    provider_id: int,
    service_id,
    service_name: str,
    name: str,
    phone: str,
    email: str | None,
    start: datetime,
    end: datetime,
    reason: str,
    source: str,
    created_at_utc: datetime,
) -> Appointment:
    """Upsert patient, verify the slot is free, create a PENDING hold, schedule notifications.

    Times are naive UTC. Raises the same 409 HTTPException as a normal booking on conflict.
    Does not commit — caller is responsible for committing.
    """
    # Local imports to avoid circular dependency if appointments/notifications ever import holds
    from services.appointments import check_conflicts_for_create
    from services.notifications import schedule_hold_create_notifications

    check_conflicts_for_create(db, clinic=clinic, provider_id=provider_id, start=start, end=end)
    patient = upsert_patient_by_phone(db, clinic_id=clinic.id, name=name, phone=phone, email=email)
    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic.id,
        patient_id=patient.id,
        provider_id=provider_id,
        service_id=service_id,
        start_time=start,
        end_time=end,
        reason_note=reason,
        status=AppointmentStatus.PENDING,
        hold_expiry_at=compute_hold_expiry(db, clinic, created_at_utc),
        patient_confirmed=False,
        source=source,
    )
    db.add(appt)
    db.flush()
    provider = appt.provider
    schedule_hold_create_notifications(
        background_tasks,
        patient=patient,
        provider=provider,
        appointment=appt,
        clinic=clinic,
        service_name=service_name,
        source=source,
    )
    return appt


def _split_name(name: str):
    parts = (name or "").strip().split()
    if not parts:
        return "Patient", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def upsert_patient_by_phone(db: Session, *, clinic_id: str, name: str,
                            phone: str, email: str | None) -> Patient:
    """Find a clinic patient by phone or create one. Does not commit."""
    existing = (
        db.query(Patient)
        .filter(Patient.clinic_id == clinic_id, Patient.phone == phone)
        .first()
    )
    if existing is not None:
        if email and not existing.email:
            existing.email = email
        return existing
    first, last = _split_name(name)
    patient = Patient(
        id=str(uuid.uuid4()), clinic_id=clinic_id,
        first_name=first, last_name=last, phone=phone, email=email,
    )
    db.add(patient)
    db.flush()
    return patient

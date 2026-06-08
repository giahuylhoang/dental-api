from datetime import datetime, timedelta, time as dtime
import pytz
from sqlalchemy.orm import Session
from database.models import Clinic
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

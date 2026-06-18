from datetime import datetime, time
import pytz
from fastapi import BackgroundTasks
from database.models import Clinic, Provider, AppointmentStatus
from database.v1_1.models import ClinicOperatingHours
from services.holds import create_hold

TZ = pytz.timezone("America/Edmonton")


def _seed(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton", contact_phone="4032476222"))
    for dow in range(5):
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(9, 0), close_at=time(17, 0), is_closed=False))
    for dow in (5, 6):
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(0, 0), close_at=time(0, 0), is_closed=True))
    db.add(Provider(clinic_id="mm", name="Soheil", title="Denturist", is_active=True))
    db.commit()
    return db.query(Clinic).get("mm"), db.query(Provider).filter_by(clinic_id="mm").first()


def _utc(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).astimezone(pytz.utc).replace(tzinfo=None)


def test_create_hold_makes_pending_with_expiry(db_session):
    clinic, prov = _seed(db_session)
    bg = BackgroundTasks()
    appt = create_hold(
        db_session, bg, clinic=clinic, provider_id=prov.id, service_id=None,
        service_name="Consultation", name="Jane Doe", phone="4035551234", email=None,
        start=_utc(2026, 6, 10, 14), end=_utc(2026, 6, 10, 15),
        reason="New denture consult", source="booking-web-hold",
        created_at_utc=_utc(2026, 6, 9, 10),
    )
    db_session.commit()
    assert appt.status == AppointmentStatus.PENDING
    assert appt.source == "booking-web-hold"
    assert appt.patient_confirmed is False
    assert appt.hold_expiry_at is not None


def test_create_hold_rejects_conflicting_slot(db_session):
    clinic, prov = _seed(db_session)
    bg = BackgroundTasks()
    create_hold(db_session, bg, clinic=clinic, provider_id=prov.id, service_id=None,
                service_name="Consultation", name="A", phone="4035550000", email=None,
                start=_utc(2026, 6, 10, 14), end=_utc(2026, 6, 10, 15),
                reason="x", source="booking-web-hold", created_at_utc=_utc(2026, 6, 9, 10))
    db_session.commit()
    import pytest
    from fastapi import HTTPException   # <-- REAL exception: fastapi.HTTPException(status_code=409)
    with pytest.raises(HTTPException) as ei:
        create_hold(db_session, bg, clinic=clinic, provider_id=prov.id, service_id=None,
                    service_name="Consultation", name="B", phone="4035551111", email=None,
                    start=_utc(2026, 6, 10, 14), end=_utc(2026, 6, 10, 15),
                    reason="x", source="booking-web-hold", created_at_utc=_utc(2026, 6, 9, 10))
    assert ei.value.status_code == 409

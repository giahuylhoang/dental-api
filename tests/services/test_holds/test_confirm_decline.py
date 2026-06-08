from datetime import datetime, time
import pytz
from fastapi import BackgroundTasks
from database.models import Clinic, Provider, AppointmentStatus
from database.v1_1.models import ClinicOperatingHours
from services.holds import create_hold, confirm_hold, decline_hold

TZ = pytz.timezone("America/Edmonton")

def _seed(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton", contact_phone="4032476222"))
    for dow in range(5):
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(9, 0), close_at=time(17, 0), is_closed=False))
    db.add(Provider(clinic_id="mm", name="Soheil", title="Denturist", is_active=True))
    db.commit()
    return db.query(Clinic).get("mm"), db.query(Provider).filter_by(clinic_id="mm").first()

def _utc(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).astimezone(pytz.utc).replace(tzinfo=None)

def _make_hold(db, clinic, prov):
    bg = BackgroundTasks()
    a = create_hold(db, bg, clinic=clinic, provider_id=prov.id, service_id=None,
                    service_name="Consultation", name="Jane Doe", phone="4035551234", email=None,
                    start=_utc(2026, 6, 10, 14), end=_utc(2026, 6, 10, 15),
                    reason="x", source="booking-web-hold", created_at_utc=_utc(2026, 6, 9, 10))
    db.commit()
    return a

def test_confirm_promotes_to_scheduled(db_session):
    clinic, prov = _seed(db_session)
    a = _make_hold(db_session, clinic, prov)
    bg = BackgroundTasks()
    confirm_hold(db_session, bg, clinic=clinic, appointment=a, service_name="Consultation")
    db_session.commit()
    assert a.status == AppointmentStatus.SCHEDULED
    assert a.hold_expiry_at is None

def test_decline_cancels_and_frees_slot(db_session):
    clinic, prov = _seed(db_session)
    a = _make_hold(db_session, clinic, prov)
    decline_hold(db_session, clinic=clinic, appointment=a)
    db_session.commit()
    assert a.status == AppointmentStatus.CANCELLED

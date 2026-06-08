from datetime import datetime, timedelta
from database.models import Clinic, Provider, Patient, Appointment, AppointmentStatus
from api.v2.scheduling.reminder_scheduler import expire_pending_holds


def test_sweep_cancels_expired_pending(db_session):
    db_session.add_all([
        Clinic(id="mm", name="MM", timezone="America/Edmonton"),
        Provider(id=101, clinic_id="mm", name="S", title="Denturist", is_active=True),
        Patient(id="p1", first_name="A", last_name="B", clinic_id="mm", phone="403"),
    ])
    db_session.commit()
    past = datetime.utcnow() - timedelta(hours=1)
    future = datetime.utcnow() + timedelta(hours=5)
    db_session.add_all([
        Appointment(id="expired", clinic_id="mm", patient_id="p1", provider_id=101,
                    start_time=datetime(2026, 6, 10, 21), end_time=datetime(2026, 6, 10, 22),
                    status=AppointmentStatus.PENDING, hold_expiry_at=past, source="booking-web-hold"),
        Appointment(id="fresh", clinic_id="mm", patient_id="p1", provider_id=101,
                    start_time=datetime(2026, 6, 11, 21), end_time=datetime(2026, 6, 11, 22),
                    status=AppointmentStatus.PENDING, hold_expiry_at=future, source="booking-web-hold"),
    ])
    db_session.commit()
    n = expire_pending_holds(db_session)
    assert n == 1
    assert db_session.query(Appointment).get("expired").status == AppointmentStatus.CANCELLED
    assert db_session.query(Appointment).get("fresh").status == AppointmentStatus.PENDING

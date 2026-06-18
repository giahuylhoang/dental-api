from datetime import datetime
from database.models import Appointment, AppointmentStatus, Clinic, Provider, Patient


def test_appointment_has_hold_fields(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    pat = Patient(id="pat-c1", first_name="T", last_name="P", clinic_id="c1")
    db_session.add_all([c, p, pat])
    db_session.commit()
    a = Appointment(
        clinic_id="c1", patient_id="pat-c1", provider_id=p.id,
        start_time=datetime(2026, 6, 9, 16, 0), end_time=datetime(2026, 6, 9, 17, 0),
        status=AppointmentStatus.PENDING,
        hold_expiry_at=datetime(2026, 6, 10, 23, 0),
        patient_confirmed=False,
        source="booking-web-hold",
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    assert a.hold_expiry_at == datetime(2026, 6, 10, 23, 0)
    assert a.patient_confirmed is False
    assert a.source == "booking-web-hold"

from datetime import datetime, timedelta
from database.models import Clinic, Provider, Patient, Appointment, AppointmentStatus
from services.appointments import check_conflicts_for_create
import pytest
from fastapi import HTTPException


def _seed(db):
    db.add_all([
        Clinic(id="mm", name="MM", timezone="America/Edmonton"),
        Provider(id=101, clinic_id="mm", name="S", title="Denturist", is_active=True),
        Patient(id="p1", first_name="A", last_name="B", clinic_id="mm", phone="403"),
    ])
    db.commit()
    return db.query(Clinic).get("mm")


def test_expired_pending_hold_does_not_block(db_session):
    clinic = _seed(db_session)
    past = datetime.utcnow() - timedelta(hours=1)
    db_session.add(Appointment(
        clinic_id="mm", patient_id="p1", provider_id=101,
        start_time=datetime(2026, 6, 10, 21, 0), end_time=datetime(2026, 6, 10, 22, 0),
        status=AppointmentStatus.PENDING, hold_expiry_at=past, source="booking-web-hold"))
    db_session.commit()
    check_conflicts_for_create(db_session, clinic=clinic, provider_id=101,
                               start=datetime(2026, 6, 10, 21, 0), end=datetime(2026, 6, 10, 22, 0))


def test_unexpired_pending_hold_still_blocks(db_session):
    clinic = _seed(db_session)
    future = datetime.utcnow() + timedelta(hours=5)
    db_session.add(Appointment(
        clinic_id="mm", patient_id="p1", provider_id=101,
        start_time=datetime(2026, 6, 10, 21, 0), end_time=datetime(2026, 6, 10, 22, 0),
        status=AppointmentStatus.PENDING, hold_expiry_at=future, source="booking-web-hold"))
    db_session.commit()
    with pytest.raises(HTTPException) as ei:
        check_conflicts_for_create(db_session, clinic=clinic, provider_id=101,
                                   start=datetime(2026, 6, 10, 21, 0), end=datetime(2026, 6, 10, 22, 0))
    assert ei.value.status_code == 409

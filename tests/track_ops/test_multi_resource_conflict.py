"""Test multi-resource conflict detection: operatory + provider."""
import pytest
from database.models import Patient, Provider, Service, Appointment, AppointmentStatus, DEFAULT_CLINIC_ID
from database.ops.models import Operatory


def _make_patient(db, name="Pat"):
    p = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name=name, phone="555")
    db.add(p)
    db.flush()
    return p


def _make_provider(db, name="Dr A"):
    p = Provider(clinic_id=DEFAULT_CLINIC_ID, name=name)
    db.add(p)
    db.flush()
    return p


def _make_operatory(db, name="Op 1"):
    op = Operatory(clinic_id=DEFAULT_CLINIC_ID, name=name)
    db.add(op)
    db.flush()
    return op


def test_provider_busy_blocks_booking(client, db_session):
    """Provider conflict → 409 even if operatory is free."""
    patient = _make_patient(db_session)
    provider = _make_provider(db_session)
    op = _make_operatory(db_session)
    db_session.commit()

    # Book first appointment
    r1 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T10:00:00",
        "end_time": "2026-06-01T11:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op.id,
    })
    assert r1.status_code == 201

    # Second appointment: same provider, different operatory → 409
    op2 = _make_operatory(db_session, "Op 2")
    db_session.commit()

    r2 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T10:30:00",
        "end_time": "2026-06-01T11:30:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op2.id,
    })
    assert r2.status_code == 409


def test_operatory_busy_blocks_booking(client, db_session):
    """Operatory conflict → 409 even if provider is free."""
    patient = _make_patient(db_session)
    provider1 = _make_provider(db_session, "Dr A")
    provider2 = _make_provider(db_session, "Dr B")
    op = _make_operatory(db_session)
    db_session.commit()

    # Book first appointment with provider1 in op
    r1 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T10:00:00",
        "end_time": "2026-06-01T11:00:00",
        "patient_id": patient.id,
        "provider_id": provider1.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op.id,
    })
    assert r1.status_code == 201

    # Second appointment: different provider, same operatory → 409
    r2 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T10:30:00",
        "end_time": "2026-06-01T11:30:00",
        "patient_id": patient.id,
        "provider_id": provider2.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op.id,
    })
    assert r2.status_code == 409


def test_no_conflict_different_times(client, db_session):
    """Non-overlapping times → both succeed."""
    patient = _make_patient(db_session)
    provider = _make_provider(db_session)
    op = _make_operatory(db_session)
    db_session.commit()

    r1 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T09:00:00",
        "end_time": "2026-06-01T10:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op.id,
    })
    assert r1.status_code == 201

    r2 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-06-01T10:00:00",
        "end_time": "2026-06-01T11:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Pat",
        "service_name": "Consult",
        "reason": "test",
        "operatory_id": op.id,
    })
    assert r2.status_code == 201

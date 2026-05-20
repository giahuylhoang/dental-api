"""Test recurring appointment generation."""
import pytest
from database.models import Patient, Provider, DEFAULT_CLINIC_ID


def _make_patient(db):
    p = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Rec", phone="555")
    db.add(p)
    db.flush()
    return p


def _make_provider(db):
    p = Provider(clinic_id=DEFAULT_CLINIC_ID, name="Dr Rec")
    db.add(p)
    db.flush()
    return p


def test_weekly_recurrence_generates_4(client, db_session):
    """RRULE FREQ=WEEKLY;COUNT=4 produces 4 appointments."""
    patient = _make_patient(db_session)
    provider = _make_provider(db_session)
    db_session.commit()

    r = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-01T10:00:00",
        "end_time": "2026-07-01T11:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Rec",
        "service_name": "Consult",
        "reason": "test",
        "recurrence_rule": "FREQ=WEEKLY;COUNT=4",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["generated_count"] == 4
    assert data["recurrence_id"] is not None


def test_recurrence_conflict_fails(client, db_session):
    """Busy block on one occurrence → 409 for the whole series."""
    patient = _make_patient(db_session)
    provider = _make_provider(db_session)
    db_session.commit()

    # Block week 2 (2026-07-08)
    block_patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Block", phone="556")
    db_session.add(block_patient)
    db_session.flush()
    db_session.commit()

    r_block = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-08T10:00:00",
        "end_time": "2026-07-08T11:00:00",
        "patient_id": block_patient.id,
        "provider_id": provider.id,
        "patient_name": "Block",
        "service_name": "Block",
        "reason": "block",
    })
    assert r_block.status_code == 201

    # Now try recurring series that hits week 2
    r = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-01T10:00:00",
        "end_time": "2026-07-01T11:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "Rec",
        "service_name": "Consult",
        "reason": "test",
        "recurrence_rule": "FREQ=WEEKLY;COUNT=4",
    })
    assert r.status_code == 409

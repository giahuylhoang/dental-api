"""Booking endpoints reject overlaps with provider busy blocks.

Both POST /api/calendar/events and PUT /api/appointments/{id}/reschedule must
return 409 with `{"error": "Provider busy", ..., "busy_block": {...}}` when the
requested window overlaps a recurring busy block.
"""
import pytest

from database.models import (
    Provider, Service, ProviderBusyBlock, Patient, DEFAULT_CLINIC_ID,
)


HDR = {"X-Clinic-Id": "default"}


@pytest.fixture
def fixtures(client, db_session):
    """Provider + service + patient + busy block (Mon 12:00–13:00 'Lunch')."""
    provider = Provider(id=701, clinic_id=DEFAULT_CLINIC_ID, name="Smith",
                        title="Dr", specialty="General", is_active=True)
    service = Service(id=701, clinic_id=DEFAULT_CLINIC_ID, name="Consult",
                      description="Consultation", duration_min=30, base_price=100)
    db_session.add_all([provider, service])
    db_session.flush()
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=701, weekday=0,
        start_hour=12, start_minute=0, end_hour=13, end_minute=0, label="Lunch",
    ))
    db_session.commit()
    pat = client.post("/api/patients", json={
        "first_name": "Block", "last_name": "Test", "phone": "5550007007",
    }, headers=HDR).json()
    return {
        "provider_id": provider.id,
        "service_id": service.id,
        "patient_id": pat["id"],
    }


# 2026-03-09 is a Monday (weekday=0), matches the busy-block weekday.

def test_create_appointment_409_when_inside_busy_block(client, fixtures):
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T12:30:00-06:00",
        "end_time": "2026-03-09T13:00:00-06:00",
        "patient_id": fixtures["patient_id"],
        "provider_id": fixtures["provider_id"],
        "service_id": fixtures["service_id"],
        "patient_name": "Block Test",
        "service_name": "Consult",
        "reason": "Should fail",
    }, headers=HDR)
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["error"] == "Provider busy"
    assert body["busy_block"]["label"] == "Lunch"
    assert body["busy_block"]["weekday"] == 0
    assert body["busy_block"]["start_hour"] == 12
    assert body["busy_block"]["end_hour"] == 13


def test_create_appointment_succeeds_outside_busy_block(client, fixtures):
    """Same provider, same Monday, but outside the lunch window."""
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T14:00:00-06:00",
        "end_time": "2026-03-09T14:30:00-06:00",
        "patient_id": fixtures["patient_id"],
        "provider_id": fixtures["provider_id"],
        "service_id": fixtures["service_id"],
        "patient_name": "Block Test",
        "service_name": "Consult",
        "reason": "OK",
    }, headers=HDR)
    assert r.status_code == 200
    assert r.json()["status"] in {"SCHEDULED", "scheduled"}


def test_reschedule_409_when_target_inside_busy_block(client, fixtures):
    """Book outside the block, then reschedule into it → 409."""
    apt = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T14:00:00-06:00",
        "end_time": "2026-03-09T14:30:00-06:00",
        "patient_id": fixtures["patient_id"],
        "provider_id": fixtures["provider_id"],
        "service_id": fixtures["service_id"],
        "patient_name": "Block Test",
        "service_name": "Consult",
        "reason": "OK",
    }, headers=HDR).json()
    apt_id = apt["appointment_id"]
    r = client.put(f"/api/appointments/{apt_id}/reschedule", json={
        "start_time": "2026-03-09T12:15:00-06:00",
        "end_time": "2026-03-09T12:45:00-06:00",
        "patient_id": fixtures["patient_id"],
        "provider_id": fixtures["provider_id"],
        "service_id": fixtures["service_id"],
        "patient_name": "Block Test",
        "service_name": "Consult",
        "reason": "Move into lunch",
    }, headers=HDR)
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["error"] == "Provider busy"
    assert body["busy_block"]["label"] == "Lunch"


def test_create_at_busy_block_boundary_is_allowed(client, fixtures):
    """[12:00, 13:00) busy → an appointment ending exactly at 12:00 must NOT be blocked."""
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T11:30:00-06:00",
        "end_time": "2026-03-09T12:00:00-06:00",
        "patient_id": fixtures["patient_id"],
        "provider_id": fixtures["provider_id"],
        "service_id": fixtures["service_id"],
        "patient_name": "Block Test",
        "service_name": "Consult",
        "reason": "Boundary",
    }, headers=HDR)
    assert r.status_code == 200

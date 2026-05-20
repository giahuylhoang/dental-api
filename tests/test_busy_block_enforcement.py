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


# ---------------------------------------------------------------------------
# v2 modes — multi-weekday, specific-date, bounded recurrence
# ---------------------------------------------------------------------------

import json as _json
from datetime import date, timedelta


def _make_provider_and_service(db_session, provider_id=702, service_id=702):
    p = Provider(id=provider_id, clinic_id=DEFAULT_CLINIC_ID, name="V2",
                 title="Dr", specialty="General", is_active=True)
    s = Service(id=service_id, clinic_id=DEFAULT_CLINIC_ID, name="V2 Consult",
                description="V2", duration_min=30, base_price=100)
    db_session.add_all([p, s])
    db_session.flush()
    return p.id, s.id


@pytest.fixture
def v2_fixtures(client, db_session):
    provider_id, service_id = _make_provider_and_service(db_session)
    pat = client.post("/api/patients", json={
        "first_name": "V2", "last_name": "User", "phone": "5550008008",
    }, headers=HDR).json()
    return {"provider_id": provider_id, "service_id": service_id, "patient_id": pat["id"]}


def test_multi_weekday_blocks_all_listed_days(client, db_session, v2_fixtures):
    """Block applies on Mon (0), Wed (2), Fri (4). Wed booking inside → 409."""
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        weekdays=_json.dumps([0, 2, 4]),
        start_hour=12, start_minute=0, end_hour=13, end_minute=0, label="Standup",
    ))
    db_session.commit()
    # 2026-03-11 is a Wednesday.
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-11T12:15:00-06:00",
        "end_time": "2026-03-11T12:45:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "Wed",
    }, headers=HDR)
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["busy_block"]["label"] == "Standup"
    assert body["busy_block"]["weekdays"] == [0, 2, 4]


def test_multi_weekday_does_not_block_other_days(client, db_session, v2_fixtures):
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        weekdays=_json.dumps([0, 2, 4]),
        start_hour=12, start_minute=0, end_hour=13, end_minute=0, label="Standup",
    ))
    db_session.commit()
    # 2026-03-10 is a Tuesday — not in the set.
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-10T12:15:00-06:00",
        "end_time": "2026-03-10T12:45:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "Tue",
    }, headers=HDR)
    assert r.status_code == 200


def test_specific_date_overlap_blocks_booking(client, db_session, v2_fixtures):
    """Block on a specific date — booking same date inside the window is rejected."""
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        specific_date=date(2026, 5, 23),
        start_hour=14, start_minute=0, end_hour=16, end_minute=0, label="Conference",
    ))
    db_session.commit()
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-05-23T15:00:00-06:00",
        "end_time": "2026-05-23T15:30:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "during conf",
    }, headers=HDR)
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["busy_block"]["label"] == "Conference"
    assert body["busy_block"]["specific_date"] == "2026-05-23"


def test_specific_date_other_day_does_not_block(client, db_session, v2_fixtures):
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        specific_date=date(2026, 5, 23),
        start_hour=14, start_minute=0, end_hour=16, end_minute=0, label="Conference",
    ))
    db_session.commit()
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-05-24T15:00:00-06:00",
        "end_time": "2026-05-24T15:30:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "next day",
    }, headers=HDR)
    assert r.status_code == 200


def test_recurrence_until_expires(client, db_session, v2_fixtures):
    """Recurring block bounded by recurrence_until — a Monday after that date is free."""
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        weekdays=_json.dumps([0]),  # Mondays
        recurrence_until=date(2026, 5, 20),
        start_hour=12, start_minute=0, end_hour=13, end_minute=0, label="Until-May",
    ))
    db_session.commit()
    # 2026-05-25 is a Monday — past the recurrence_until.
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-05-25T12:15:00-06:00",
        "end_time": "2026-05-25T12:45:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "after-expiry",
    }, headers=HDR)
    assert r.status_code == 200


def test_recurrence_until_still_active(client, db_session, v2_fixtures):
    """A Monday on/before recurrence_until is still blocked."""
    db_session.add(ProviderBusyBlock(
        clinic_id=DEFAULT_CLINIC_ID, provider_id=v2_fixtures["provider_id"],
        weekdays=_json.dumps([0]),
        recurrence_until=date(2026, 5, 20),
        start_hour=12, start_minute=0, end_hour=13, end_minute=0, label="Until-May",
    ))
    db_session.commit()
    # 2026-05-18 is a Monday — within the window.
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-05-18T12:15:00-06:00",
        "end_time": "2026-05-18T12:45:00-06:00",
        "patient_id": v2_fixtures["patient_id"],
        "provider_id": v2_fixtures["provider_id"],
        "service_id": v2_fixtures["service_id"],
        "patient_name": "V2 User",
        "service_name": "V2 Consult",
        "reason": "before-expiry",
    }, headers=HDR)
    assert r.status_code == 409
    assert r.json()["detail"]["busy_block"]["label"] == "Until-May"

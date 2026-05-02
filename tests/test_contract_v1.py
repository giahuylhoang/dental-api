"""
v1 contract snapshot tests.

This file is the gate for backwards compatibility. Every endpoint that existed
before the PMS/CRM expansion is locked here: response key sets, types, and a
representative happy-path round-trip.

Tracks 1-5 must keep `pytest tests/test_contract_v1.py -q` green. Adding new
endpoints under /api/v2/* is allowed; mutating any endpoint covered here is not.
"""
from __future__ import annotations

import pytest

from database.models import Provider, Service, ProviderBusyBlock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_shape(obj, expected: dict) -> None:
    """
    Assert obj is a dict whose keys form a superset of `expected.keys()`,
    and each key's value matches the type (or tuple of types) given.

    Include `type(None)` in the type tuple to allow null values.
    """
    assert isinstance(obj, dict), f"Expected dict, got {type(obj).__name__}"
    missing = [k for k in expected if k not in obj]
    assert not missing, f"Missing keys: {missing}. Got: {sorted(obj.keys())}"
    for key, types in expected.items():
        py_types = types if isinstance(types, tuple) else (types,)
        value = obj[key]
        assert isinstance(value, py_types), (
            f"Key {key!r}: expected {py_types}, got {type(value).__name__} ({value!r})"
        )


def seed_basic(db_session):
    """Seed one provider, one busy block, one service, returns (provider, service)."""
    provider = Provider(
        id=901, clinic_id="default", name="Smith", title="Dr",
        specialty="Denturist", is_active=True,
    )
    service = Service(
        id=901, clinic_id="default", name="Consult",
        description="Consultation", duration_min=30, base_price=100,
    )
    db_session.add_all([provider, service])
    db_session.flush()
    db_session.add(ProviderBusyBlock(
        clinic_id="default", provider_id=901, weekday=6,
        start_hour=0, start_minute=0, end_hour=23, end_minute=59,
    ))
    db_session.commit()
    return provider, service


# ---------------------------------------------------------------------------
# Health & debug
# ---------------------------------------------------------------------------

def test_v1_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_shape(r.json(), {"status": str})


def test_v1_debug_db_info(client):
    r = client.get("/api/debug/db-info")
    assert r.status_code == 200
    assert_shape(r.json(), {
        "database_host": (str, type(None)),
        "database_name": (str, type(None)),
        "provider_count": int,
    })


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

def test_v1_providers_list_and_get(client, db_session):
    seed_basic(db_session)
    r = client.get("/api/providers")
    assert r.status_code == 200
    assert isinstance(r.json(), list) and len(r.json()) == 1
    assert_shape(r.json()[0], {
        "id": int,
        "name": str,
        "title": (str, type(None)),
        "specialty": (str, type(None)),
        "is_active": bool,
    })

    r = client.get("/api/providers/901")
    assert r.status_code == 200
    assert_shape(r.json(), {
        "id": int, "name": str, "title": (str, type(None)),
        "specialty": (str, type(None)), "is_active": bool,
    })

    r = client.get("/api/providers/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

def test_v1_services_list_and_get(client, db_session):
    seed_basic(db_session)
    r = client.get("/api/services")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list) and body
    assert_shape(body[0], {
        "id": int, "name": str,
        "description": (str, type(None)),
        "duration_min": (int, type(None)),
        "base_price": (float, type(None)),
    })

    r = client.get("/api/services/901")
    assert r.status_code == 200
    assert_shape(r.json(), {
        "id": int, "name": str,
        "description": (str, type(None)),
        "duration_min": (int, type(None)),
        "base_price": (float, type(None)),
    })

    assert client.get("/api/services/99999").status_code == 404


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

PATIENT_KEYS = {
    "id": str, "first_name": (str, type(None)), "last_name": (str, type(None)),
    "phone": (str, type(None)), "email": (str, type(None)),
}


def test_v1_patient_crud(client):
    create = client.post("/api/patients", json={
        "first_name": "Anna", "last_name": "Lee",
        "phone": "5550001111", "email": "anna@example.com",
        "consent_approved": True,
    })
    assert create.status_code == 200
    pid = create.json()["id"]
    assert_shape(create.json(), PATIENT_KEYS)

    got = client.get(f"/api/patients/{pid}")
    assert got.status_code == 200
    assert_shape(got.json(), PATIENT_KEYS)

    listed = client.get("/api/patients", params={"phone": "5550001111"})
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    assert any(p["id"] == pid for p in listed.json())

    upd = client.put(f"/api/patients/{pid}", json={"email": "new@example.com"})
    assert upd.status_code == 200
    assert upd.json()["email"] == "new@example.com"

    assert client.get("/api/patients/does-not-exist").status_code == 404


def test_v1_patient_verify(client):
    client.post("/api/patients", json={
        "first_name": "V", "last_name": "Test",
        "phone": "5559998888", "dob": "1990-05-15",
    })
    ok = client.post("/api/patients/verify", json={
        "phone": "5559998888", "dob": "1990-05-15",
    })
    assert ok.status_code == 200
    assert_shape(ok.json(), {"patient_id": str, "verified": bool})

    # Wrong DOB → 404 (no data leak)
    bad = client.post("/api/patients/verify", json={
        "phone": "5559998888", "dob": "1991-01-01",
    })
    assert bad.status_code == 404

    # Bad date format → 400
    fmt = client.post("/api/patients/verify", json={
        "phone": "5559998888", "dob": "not-a-date",
    })
    assert fmt.status_code == 400


# ---------------------------------------------------------------------------
# Calendar slots
# ---------------------------------------------------------------------------

def test_v1_calendar_slots_all_providers(client, db_session):
    seed_basic(db_session)
    r = client.get("/api/calendar/slots", params={
        "start_datetime": "2026-03-09T09:00:00-06:00",
        "end_datetime": "2026-03-09T12:00:00-06:00",
        "slot_minutes": 30,
    })
    assert r.status_code == 200
    body = r.json()
    assert "providers" in body
    assert isinstance(body["providers"], list)
    if body["providers"]:
        assert_shape(body["providers"][0], {
            "provider_id": int,
            "title": (str, type(None)),
            "slots": list,
        })


def test_v1_calendar_slots_specific_provider(client, db_session):
    seed_basic(db_session)
    r = client.get("/api/calendar/slots", params={
        "start_datetime": "2026-03-09T09:00:00-06:00",
        "end_datetime": "2026-03-09T12:00:00-06:00",
        "provider_id": 901,
        "slot_minutes": 30,
    })
    assert r.status_code == 200
    body = r.json()
    assert "provider" in body and "slots" in body
    assert_shape(body["provider"], {
        "provider_id": int, "title": (str, type(None)),
    })
    assert isinstance(body["slots"], list)


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

APPOINTMENT_DETAIL_KEYS = {
    "id": str, "patient_id": str, "provider_id": int,
    "service_id": (int, type(None)),
    "provider_name": (str, type(None)),
    "service_name": (str, type(None)),
    "start_time": str, "end_time": str,
    "reason_note": (str, type(None)),
    "status": str,
    "calendar_event_id": (str, type(None)),
}

APPOINTMENT_RESPONSE_KEYS = {
    "appointment_id": str,
    "calendar_event_id": (str, type(None)),
    "calendar_link": (str, type(None)),
    "status": str,
}


@pytest.fixture
def booked(client, db_session):
    """Create one provider/service/patient/appointment, return ids."""
    provider, service = seed_basic(db_session)
    pat = client.post("/api/patients", json={
        "first_name": "Apt", "last_name": "Test",
        "phone": "5550009999",
    }).json()
    apt = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T10:00:00-06:00",
        "end_time": "2026-03-09T10:30:00-06:00",
        "patient_id": pat["id"],
        "provider_id": provider.id,
        "service_id": service.id,
        "patient_name": "Apt Test",
        "service_name": service.name,
        "reason": "Checkup",
    }).json()
    return {"patient_id": pat["id"], "provider_id": provider.id,
            "service_id": service.id, "appointment_id": apt["appointment_id"]}


def test_v1_create_appointment_response_shape(client, db_session):
    provider, service = seed_basic(db_session)
    pat = client.post("/api/patients", json={"first_name": "X", "last_name": "Y", "phone": "5551112222"}).json()
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-10T10:00:00-06:00",
        "end_time": "2026-03-10T10:30:00-06:00",
        "patient_id": pat["id"], "provider_id": provider.id, "service_id": service.id,
        "patient_name": "X Y", "service_name": service.name, "reason": "Test",
    })
    assert r.status_code == 200
    assert_shape(r.json(), APPOINTMENT_RESPONSE_KEYS)


def test_v1_appointments_list_and_get(client, booked):
    r = client.get("/api/appointments")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list) and body
    assert_shape(body[0], APPOINTMENT_DETAIL_KEYS)

    r = client.get(f"/api/appointments/{booked['appointment_id']}")
    assert r.status_code == 200
    assert_shape(r.json(), APPOINTMENT_DETAIL_KEYS)

    # Filter by patient
    r = client.get("/api/appointments", params={"patient_id": booked["patient_id"]})
    assert r.status_code == 200
    assert all(a["patient_id"] == booked["patient_id"] for a in r.json())


def test_v1_appointment_status_update(client, booked):
    r = client.put(
        f"/api/appointments/{booked['appointment_id']}/status",
        json={"status": "CONFIRMED"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"

    bad = client.put(
        f"/api/appointments/{booked['appointment_id']}/status",
        json={"status": "NOT_A_STATUS"},
    )
    assert bad.status_code == 400


def test_v1_appointment_cancel(client, booked):
    r = client.put(f"/api/appointments/{booked['appointment_id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"


def test_v1_appointment_update_dict(client, booked):
    r = client.put(
        f"/api/appointments/{booked['appointment_id']}",
        json={"reason_note": "rescheduled note"},
    )
    assert r.status_code == 200
    assert r.json()["reason_note"] == "rescheduled note"


def test_v1_appointment_reschedule(client, booked, db_session):
    r = client.put(
        f"/api/appointments/{booked['appointment_id']}/reschedule",
        json={
            "start_time": "2026-03-11T10:00:00-06:00",
            "end_time": "2026-03-11T10:30:00-06:00",
            "patient_id": booked["patient_id"],
            "provider_id": booked["provider_id"],
            "service_id": booked["service_id"],
            "patient_name": "Apt Test",
            "service_name": "Consult",
            "reason": "Reschedule",
        },
    )
    assert r.status_code == 200
    assert_shape(r.json(), {
        "old_appointment_id": str, "new_appointment_id": str, "status": str,
    })
    assert r.json()["status"] == "RESCHEDULED"


def test_v1_appointment_delete(client, booked):
    r = client.delete(f"/api/appointments/{booked['appointment_id']}")
    assert r.status_code == 200
    assert_shape(r.json(), {"message": str, "appointment_id": str})

    assert client.get(f"/api/appointments/{booked['appointment_id']}").status_code == 404


def test_v1_appointment_conflict_409(client, booked):
    r = client.post("/api/calendar/events", json={
        "start_time": "2026-03-09T10:00:00-06:00",
        "end_time": "2026-03-09T10:30:00-06:00",
        "patient_id": booked["patient_id"],
        "provider_id": booked["provider_id"],
        "service_id": booked["service_id"],
        "patient_name": "Apt Test",
        "service_name": "Consult",
        "reason": "Conflict",
    })
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert isinstance(detail, dict)
    assert "conflicting_appointments" in detail
    assert "requested_time" in detail


def test_v1_appointment_bulk_delete_dry_run(client, booked):
    r = client.delete(
        "/api/appointments/bulk/date/2026-03-09",
        params={"dry_run": "true"},
    )
    assert r.status_code == 200
    assert_shape(r.json(), {
        "message": str, "date": str,
        "appointments_found": int, "deleted": int,
    })


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

LEAD_KEYS = {
    "id": str, "name": (str, type(None)),
    "phone": (str, type(None)), "email": (str, type(None)),
    "source": (str, type(None)), "status": str,
    "notes": (str, type(None)),
    "created_at": str, "updated_at": str,
}


def test_v1_lead_crud(client):
    c = client.post("/api/leads", json={
        "name": "Lead Test", "phone": "5557770000",
        "email": "lead@example.com", "source": "google",
    })
    assert c.status_code == 200
    assert_shape(c.json(), LEAD_KEYS)
    lid = c.json()["id"]

    g = client.get(f"/api/leads/{lid}")
    assert g.status_code == 200 and g.json()["id"] == lid

    li = client.get("/api/leads")
    assert li.status_code == 200 and any(x["id"] == lid for x in li.json())

    u = client.put(f"/api/leads/{lid}", json={"notes": "hot lead"})
    assert u.status_code == 200 and u.json()["notes"] == "hot lead"

    s = client.put(f"/api/leads/{lid}/status", json={"status": "CONTACTED"})
    assert s.status_code == 200 and s.json()["status"] == "CONTACTED"

    bad = client.put(f"/api/leads/{lid}/status", json={"status": "BAD"})
    assert bad.status_code == 400


# ---------------------------------------------------------------------------
# Clinics (multi-tenant)
# ---------------------------------------------------------------------------

CLINIC_KEYS = {
    "id": str, "name": str,
    "timezone": (str, type(None)),
    "working_hour_start": (int, type(None)),
    "working_hour_end": (int, type(None)),
    "address": (str, type(None)),
    "contact_phone": (str, type(None)),
    "booking_notification_email": (str, type(None)),
}


def test_v1_clinic_get_default_via_no_header(client):
    """X-Clinic-Id default behavior: no header → default clinic."""
    r = client.get("/api/clinics/me")
    assert r.status_code == 200
    assert r.json()["id"] == "default"
    assert_shape(r.json(), CLINIC_KEYS)


def test_v1_clinic_create_and_patch(client):
    c = client.post("/api/clinics", json={
        "id": "v1-test-clinic", "name": "v1 test",
        "timezone": "America/Edmonton",
    })
    assert c.status_code == 200
    assert_shape(c.json(), CLINIC_KEYS)

    # Duplicate → 409
    dup = client.post("/api/clinics", json={
        "id": "v1-test-clinic", "name": "again",
    })
    assert dup.status_code == 409

    # Patch via X-Clinic-Id header
    p = client.patch(
        "/api/clinics/me",
        headers={"X-Clinic-Id": "v1-test-clinic"},
        json={"address": "1 Test Ave", "contact_phone": "403-000-0000"},
    )
    assert p.status_code == 200
    assert p.json()["address"] == "1 Test Ave"
    assert p.json()["contact_phone"] == "403-000-0000"


def test_v1_unknown_clinic_404(client):
    r = client.get("/api/patients", headers={"X-Clinic-Id": "ghost-clinic"})
    assert r.status_code == 404

"""
API tests for dental-api endpoints.

Run from dental-api project root:
  .venv/bin/python -m pytest tests/ -v
  # or: pip install -r requirements-dev.txt && pytest tests/ -v
"""
import pytest

import api.main as api_main

from database.models import (
    DEFAULT_CLINIC_ID,
    Provider,
    ProviderBusyBlock,
    Service,
)


# ---------------------------------------------------------------------------
# Health & debug
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/health", "/api/debug/db-info"])
def test_health_and_debug(client, path):
    response = client.get(path)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------

def test_list_providers_empty(client):
    response = client.get("/api/providers")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

def test_list_services_empty(client):
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Patients (create_patient, get_patient, list)
# ---------------------------------------------------------------------------

def test_create_patient_and_get(client):
    """Create patient then get by id - ensures write path works (not readonly)."""
    payload = {
        "first_name": "Asim",
        "last_name": "Ahmed",
        "phone": "83682990959",
        "consent_approved": True,
    }
    create_resp = client.post("/api/patients", json=payload)
    assert create_resp.status_code == 200, create_resp.text
    data = create_resp.json()
    assert "id" in data
    assert data["first_name"] == "Asim"
    assert data["last_name"] == "Ahmed"
    assert data["phone"] == "83682990959"

    patient_id = data["id"]
    get_resp = client.get(f"/api/patients/{patient_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == patient_id
    assert get_resp.json()["first_name"] == "Asim"


def test_get_patient_404(client):
    response = client.get("/api/patients/non-existent-id")
    assert response.status_code == 404


def test_list_patients_by_phone(client):
    client.post(
        "/api/patients",
        json={"first_name": "A", "last_name": "B", "phone": "5551234567"},
    )
    response = client.get("/api/patients", params={"phone": "5551234567"})
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["phone"] == "5551234567"


def test_create_patient_minimal(client):
    """Minimal payload: only required fields for agent-style create."""
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "4031112233",
        "consent_approved": True,
    }
    resp = client.post("/api/patients", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Jane"
    assert body["last_name"] == "Doe"
    assert body["phone"] == "4031112233"
    assert body["id"] is not None


# ---------------------------------------------------------------------------
# Providers, Services, Slots
# ---------------------------------------------------------------------------


def seed_providers_and_services(db_session):
    provider1 = Provider(
        id=1,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Johnson",
        title="Dr",
        specialty="General",
        is_active=True,
    )
    provider2 = Provider(
        id=2,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Smith",
        title="Mr",
        specialty="Dental Assistant",
        is_active=True,
    )
    service1 = Service(
        id=1,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Routine Cleaning",
        description="Test service",
        duration_min=60,
        base_price=150.0,
    )
    db_session.add_all([provider1, provider2, service1])
    db_session.commit()
    return provider1, provider2, service1


def test_providers_and_services_after_seeding(client, db_session):
    p1, p2, s1 = seed_providers_and_services(db_session)

    providers_resp = client.get("/api/providers")
    assert providers_resp.status_code == 200
    providers = providers_resp.json()
    assert len(providers) == 2

    provider_resp = client.get(f"/api/providers/{p1.id}")
    assert provider_resp.status_code == 200
    assert provider_resp.json()["title"] == p1.title

    services_resp = client.get("/api/services")
    assert services_resp.status_code == 200
    services = services_resp.json()
    assert len(services) == 1
    assert services[0]["id"] == s1.id


def test_calendar_slots_per_provider(client, db_session):
    seed_providers_and_services(db_session)

    start = "2026-03-10T09:00:00-06:00"
    end = "2026-03-10T12:00:00-06:00"

    # Without provider_id -> per-provider response including titles
    resp = client.get(
        "/api/calendar/slots",
        params={"start_datetime": start, "end_datetime": end, "slot_minutes": 30},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data
    assert len(data["providers"]) == 2
    assert all("title" in p and "slots" in p for p in data["providers"])
    assert all(isinstance(p["slots"], list) for p in data["providers"])
    # 09:00, 09:30, 10:00, 10:30, 11:00, 11:30 (end at 12:00)
    assert all(len(p["slots"]) == 6 for p in data["providers"])

    # With provider_id -> single-provider response
    resp2 = client.get(
        "/api/calendar/slots",
        params={
            "start_datetime": start,
            "end_datetime": end,
            "provider_id": 1,
            "slot_minutes": 30,
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "provider" in data2
    assert data2["provider"]["provider_id"] == 1
    assert len(data2["slots"]) == 6


# ---------------------------------------------------------------------------
# Multi-tenant: market-mall-denture
# ---------------------------------------------------------------------------


def test_market_mall_denture_clinic_slots_with_busy_blocks(client_market_mall):
    """Slots for Friday: Soheil 15:00-17:00 only, Nadeem 9:00-12:00 only."""
    # 2026-03-20 is a Friday
    start = "2026-03-20T09:00:00-06:00"
    end = "2026-03-20T17:00:00-06:00"
    headers = {"X-Clinic-Id": "market-mall-denture"}

    resp = client_market_mall.get(
        "/api/calendar/slots",
        params={"start_datetime": start, "end_datetime": end, "slot_minutes": 30},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data
    providers = {p["provider_id"]: p for p in data["providers"]}

    # Soheil (101): within clinic hours Fri 15-17 only (busy before 15:00; after 18:30 is outside 9-17)
    soheil = providers.get(101)
    assert soheil is not None
    slots = soheil["slots"]
    assert all("15:00" in s or "15:30" in s or "16:00" in s or "16:30" in s for s in slots)
    assert len(slots) == 4  # 15:00, 15:30, 16:00, 16:30

    # Nadeem (102): available Fri 9-12 only (busy 12-17)
    nadeem = providers.get(102)
    assert nadeem is not None
    slots_102 = nadeem["slots"]
    assert all("09:" in s or "10:" in s or "11:" in s for s in slots_102)
    assert len(slots_102) == 6  # 9:00-11:30


def test_market_mall_denture_appointment_create(client_market_mall):
    """Create patient and appointment under market-mall-denture."""
    headers = {"X-Clinic-Id": "market-mall-denture"}

    patient_resp = client_market_mall.post(
        "/api/patients",
        json={"first_name": "Test", "last_name": "Patient", "consent_approved": True},
        headers=headers,
    )
    assert patient_resp.status_code == 200
    patient_id = patient_resp.json()["id"]

    apt_resp = client_market_mall.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-20T15:00:00-06:00",
            "end_time": "2026-03-20T15:30:00-06:00",
            "patient_id": patient_id,
            "provider_id": 101,
            "service_id": 700,
            "patient_name": "Test Patient",
            "service_name": "General Consultation",
            "reason": "Consultation",
        },
        headers=headers,
    )
    assert apt_resp.status_code == 200
    body = apt_resp.json()
    assert body["status"] == "SCHEDULED"
    assert "appointment_id" in body

    get_resp = client_market_mall.get(
        f"/api/appointments/{body['appointment_id']}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    apt = get_resp.json()
    assert apt["provider_id"] == 101
    assert apt["service_id"] == 700
    assert apt["provider_name"] is not None
    assert apt["service_name"] == "General Consultation"


# ---------------------------------------------------------------------------
# ProviderBusyBlock slot logic
# ---------------------------------------------------------------------------


def test_provider_busy_block_reduces_available_slots(client, db_session):
    """Provider with Mon 9-17 busy block has no slots on Monday."""
    p1, _, _ = seed_providers_and_services(db_session)
    # Add busy block: provider 1 busy all day Monday
    db_session.add(
        ProviderBusyBlock(
            clinic_id=DEFAULT_CLINIC_ID,
            provider_id=p1.id,
            weekday=0,  # Monday
            start_hour=9,
            start_minute=0,
            end_hour=17,
            end_minute=0,
        )
    )
    db_session.commit()

    # 2026-03-09 is Monday
    start = "2026-03-09T09:00:00-06:00"
    end = "2026-03-09T17:00:00-06:00"

    resp = client.get(
        "/api/calendar/slots",
        params={
            "start_datetime": start,
            "end_datetime": end,
            "provider_id": p1.id,
            "slot_minutes": 30,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert data["provider"]["provider_id"] == p1.id
    assert len(data["slots"]) == 0


# ---------------------------------------------------------------------------
# Appointments CRUD
# ---------------------------------------------------------------------------


def create_patient_without_phone(client):
    payload = {
        "first_name": "Alice",
        "last_name": "Example",
        "consent_approved": True,
    }
    resp = client.post("/api/patients", json=payload)
    assert resp.status_code == 200
    return resp.json()["id"]


def test_appointment_create_list_get_update_cancel_status_delete(client, db_session):
    p1, _, s1 = seed_providers_and_services(db_session)
    patient_id = create_patient_without_phone(client)

    start = "2026-03-10T10:00:00-06:00"
    end = "2026-03-10T11:00:00-06:00"

    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": start,
            "end_time": end,
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "Checkup",
        },
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["status"] == "SCHEDULED"
    appointment_id = created["appointment_id"]

    list_resp = client.get("/api/appointments", params={"provider_id": p1.id})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/appointments/{appointment_id}")
    assert get_resp.status_code == 200
    apt = get_resp.json()
    assert apt["provider_id"] == p1.id
    assert apt["status"] == "SCHEDULED"
    assert "provider_name" in apt
    assert "service_name" in apt
    assert apt["provider_name"] is not None
    assert apt["service_name"] == s1.name

    update_resp = client.put(
        f"/api/appointments/{appointment_id}",
        json={"reason_note": "Updated reason"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["reason_note"] == "Updated reason"

    cancel_resp = client.put(f"/api/appointments/{appointment_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    status_resp = client.put(
        f"/api/appointments/{appointment_id}/status",
        json={"status": "CONFIRMED"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "CONFIRMED"

    delete_resp = client.delete(f"/api/appointments/{appointment_id}")
    assert delete_resp.status_code == 200

    after_delete = client.get(f"/api/appointments/{appointment_id}")
    assert after_delete.status_code == 404


def test_appointment_response_includes_provider_name_and_service_name(client, db_session):
    """GET /api/appointments and GET /api/appointments/{id} return provider_name and service_name."""
    p1, _, s1 = seed_providers_and_services(db_session)
    patient_id = create_patient_without_phone(client)

    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-10T10:00:00-06:00",
            "end_time": "2026-03-10T11:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "Checkup",
        },
    )
    assert create_resp.status_code == 200
    appointment_id = create_resp.json()["appointment_id"]

    list_resp = client.get("/api/appointments", params={"patient_id": patient_id})
    assert list_resp.status_code == 200
    apts = list_resp.json()
    assert len(apts) == 1
    assert apts[0]["provider_name"] is not None
    assert apts[0]["service_name"] == s1.name

    get_resp = client.get(f"/api/appointments/{appointment_id}")
    assert get_resp.status_code == 200
    apt = get_resp.json()
    assert apt["provider_name"] is not None
    assert apt["service_name"] == s1.name


def test_reschedule_appointment(client, db_session):
    p1, _, s1 = seed_providers_and_services(db_session)
    patient_id = create_patient_without_phone(client)

    old_start = "2026-03-11T10:00:00-06:00"
    old_end = "2026-03-11T11:00:00-06:00"
    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": old_start,
            "end_time": old_end,
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "Old appointment",
        },
    )
    old_id = create_resp.json()["appointment_id"]

    new_start = "2026-03-11T12:00:00-06:00"
    new_end = "2026-03-11T13:00:00-06:00"
    reschedule_resp = client.put(
        f"/api/appointments/{old_id}/reschedule",
        json={
            "start_time": new_start,
            "end_time": new_end,
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "Rescheduled appointment",
        },
    )
    assert reschedule_resp.status_code == 200
    body = reschedule_resp.json()
    new_id = body["new_appointment_id"]

    old_get = client.get(f"/api/appointments/{old_id}").json()
    new_get = client.get(f"/api/appointments/{new_id}").json()
    assert old_get["status"] == "RESCHEDULED"
    assert new_get["status"] == "SCHEDULED"


def test_bulk_delete_by_date(client, db_session):
    p1, _, s1 = seed_providers_and_services(db_session)
    patient_id = create_patient_without_phone(client)

    a1_start = "2026-03-12T10:00:00-06:00"
    a1_end = "2026-03-12T11:00:00-06:00"
    a2_start = "2026-03-12T14:00:00-06:00"
    a2_end = "2026-03-12T15:00:00-06:00"

    client.post(
        "/api/appointments",
        json={
            "start_time": a1_start,
            "end_time": a1_end,
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "A1",
        },
    )
    client.post(
        "/api/appointments",
        json={
            "start_time": a2_start,
            "end_time": a2_end,
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "A2",
        },
    )

    resp = client.delete("/api/appointments/bulk/date/2026-03-12")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] == 2


# ---------------------------------------------------------------------------
# Patient verify
# ---------------------------------------------------------------------------


def test_verify_patient_success(client):
    payload = {
        "first_name": "Bob",
        "last_name": "Example",
        "phone": "4031112233",
        "dob": "1990-01-01",
        "consent_approved": True,
    }
    create_resp = client.post("/api/patients", json=payload)
    patient_id = create_resp.json()["id"]

    verify_resp = client.post(
        "/api/patients/verify",
        json={"phone": "403-111-2233", "dob": "1990-01-01"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["patient_id"] == patient_id


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------


def test_leads_crud_flow(client):
    create_resp = client.post(
        "/api/leads",
        json={"name": "Lead1", "phone": "5551234567", "notes": "Initial"},
    )
    assert create_resp.status_code == 200
    lead = create_resp.json()
    lead_id = lead["id"]

    list_resp = client.get("/api/leads")
    assert list_resp.status_code == 200
    leads = list_resp.json()
    assert any(l["id"] == lead_id for l in leads)

    get_resp = client.get(f"/api/leads/{lead_id}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/leads/{lead_id}",
        json={"notes": "Updated notes", "status": "QUALIFIED"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "QUALIFIED"

    status_resp = client.put(
        f"/api/leads/{lead_id}/status",
        json={"status": "CONVERTED"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "CONVERTED"


# ---------------------------------------------------------------------------
# Clinics
# ---------------------------------------------------------------------------


def test_clinic_create_and_me(client):
    create_resp = client.post(
        "/api/clinics",
        json={"id": "clinic-a", "name": "Clinic A"},
    )
    assert create_resp.status_code == 200

    me_resp = client.get("/api/clinics/me", headers={"X-Clinic-Id": "clinic-a"})
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == "clinic-a"


def test_patch_clinic_me_updates_contact_fields(client):
    r = client.patch(
        "/api/clinics/me",
        json={
            "address": "1 Test Rd",
            "contact_phone": "555-0199",
            "booking_notification_email": "notify@test.example",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["address"] == "1 Test Rd"
    assert data["contact_phone"] == "555-0199"
    assert data["booking_notification_email"] == "notify@test.example"

    me = client.get("/api/clinics/me")
    assert me.status_code == 200
    assert me.json()["booking_notification_email"] == "notify@test.example"


def test_create_appointment_background_sms_and_clinic_email(client, db_session, monkeypatch):
    """Patch handlers bound in api.main so BackgroundTasks run instantly (no Twilio/SMTP thread)."""
    p1, _, s1 = seed_providers_and_services(db_session)

    sms_log: list = []
    email_log: list = []

    async def fake_booking_sms_delayed(*args):
        sms_log.append(args)

    async def fake_clinic_email_delayed(*args):
        email_log.append(args)

    monkeypatch.setattr(api_main, "send_booking_sms_delayed", fake_booking_sms_delayed)
    monkeypatch.setattr(api_main, "send_clinic_booking_email_delayed", fake_clinic_email_delayed)

    pr = client.patch(
        "/api/clinics/me",
        json={
            "address": "99 Clinic Ave",
            "contact_phone": "403-999-8888",
            "booking_notification_email": "desk@clinic.test",
        },
    )
    assert pr.status_code == 200

    cr = client.post(
        "/api/patients",
        json={
            "first_name": "Bob",
            "last_name": "Zed",
            "phone": "+14035551212",
            "consent_approved": True,
        },
    )
    assert cr.status_code == 200
    patient_id = cr.json()["id"]

    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-10T10:00:00-06:00",
            "end_time": "2026-03-10T11:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Bob Zed",
            "service_name": s1.name,
            "reason": "Checkup",
        },
    )
    assert create_resp.status_code == 200
    appointment_id = create_resp.json()["appointment_id"]

    assert len(sms_log) == 1
    sms_args = sms_log[0]
    assert sms_args[7] == "99 Clinic Ave"
    assert sms_args[8] == "403-999-8888"

    assert len(email_log) == 1
    email_args = email_log[0]
    assert email_args[0] == "desk@clinic.test"
    assert email_args[2] == appointment_id
    assert email_args[3] == "Bob Zed"


def test_create_appointment_clinic_email_without_patient_phone(client, db_session, monkeypatch):
    p1, _, s1 = seed_providers_and_services(db_session)

    sms_log: list = []
    email_log: list = []

    async def fake_booking_sms_delayed(*args):
        sms_log.append(args)

    async def fake_clinic_email_delayed(*args):
        email_log.append(args)

    monkeypatch.setattr(api_main, "send_booking_sms_delayed", fake_booking_sms_delayed)
    monkeypatch.setattr(api_main, "send_clinic_booking_email_delayed", fake_clinic_email_delayed)

    client.patch(
        "/api/clinics/me",
        json={"booking_notification_email": "only-email@clinic.test"},
    )
    patient_id = create_patient_without_phone(client)

    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-10T15:00:00-06:00",
            "end_time": "2026-03-10T16:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Alice Example",
            "service_name": s1.name,
            "reason": "Checkup",
        },
    )
    assert create_resp.status_code == 200

    assert len(sms_log) == 0
    assert len(email_log) == 1
    assert email_log[0][0] == "only-email@clinic.test"


def test_create_appointment_booking_email_env_recipient_without_clinic_field(
    client, db_session, monkeypatch
):
    """BOOKING_NOTIFICATION_TO alone triggers clinic email (no clinic.booking_notification_email)."""
    monkeypatch.delenv("BOOKING_NOTIFICATION_TO", raising=False)
    monkeypatch.setenv("BOOKING_NOTIFICATION_TO", "env-only-recipient@example.com")

    p1, _, s1 = seed_providers_and_services(db_session)

    email_log: list = []

    async def fake_clinic_email_delayed(*args):
        email_log.append(args)

    monkeypatch.setattr(api_main, "send_clinic_booking_email_delayed", fake_clinic_email_delayed)

    patient_id = create_patient_without_phone(client)

    create_resp = client.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-10T15:00:00-06:00",
            "end_time": "2026-03-10T16:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "Pat Env",
            "service_name": s1.name,
            "reason": "Checkup",
        },
    )
    assert create_resp.status_code == 200

    assert len(email_log) == 1
    assert email_log[0][0] == "env-only-recipient@example.com"


def test_create_appointment_booking_email_env_overrides_clinic_recipient(
    client, db_session, monkeypatch
):
    monkeypatch.setenv("BOOKING_NOTIFICATION_TO", "wins@example.com")

    p1, _, s1 = seed_providers_and_services(db_session)
    email_log: list = []

    async def fake_clinic_email_delayed(*args):
        email_log.append(args)

    monkeypatch.setattr(api_main, "send_clinic_booking_email_delayed", fake_clinic_email_delayed)

    client.patch(
        "/api/clinics/me",
        json={"booking_notification_email": "clinic-field@example.com"},
    )
    cr = client.post(
        "/api/patients",
        json={
            "first_name": "A",
            "last_name": "B",
            "phone": "+15555550100",
            "consent_approved": True,
        },
    )
    patient_id = cr.json()["id"]

    client.post(
        "/api/appointments",
        json={
            "start_time": "2026-03-11T10:00:00-06:00",
            "end_time": "2026-03-11T11:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": s1.id,
            "patient_name": "A B",
            "service_name": s1.name,
            "reason": "x",
        },
    )

    assert len(email_log) == 1
    assert email_log[0][0] == "wins@example.com"

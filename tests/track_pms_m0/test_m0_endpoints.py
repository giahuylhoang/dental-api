"""PMS Module M0 — backend gap-fill tests."""
import pytest

CLINIC_HEADERS = {"X-Clinic-Id": "default"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_patient(client):
    r = client.post("/api/patients", json={
        "first_name": "Test", "last_name": "Patient",
        "phone": "5550001111", "email": "test@example.com",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _seed_provider_and_service(client):
    """Seed a provider and service directly via DB override."""
    from database.models import Provider, Service
    from database.connection import get_db
    from api.main import app
    db = next(app.dependency_overrides[get_db]())
    p = Provider(clinic_id="default", name="Dr. Smith", title="Dr", specialty="General", is_active=True)
    db.add(p)
    db.flush()
    s = Service(clinic_id="default", name="Exam", duration_min=30, base_price=100)
    db.add(s)
    db.flush()
    db.commit()
    return p.id, s.id


def _create_appointment_db(client, patient_id, provider_id, service_id, chief_complaint=None):
    """Create appointment directly via DB to avoid v1 API required-field constraints."""
    from database.models import Appointment, AppointmentStatus
    from database.connection import get_db
    from api.main import app
    from datetime import datetime
    db = next(app.dependency_overrides[get_db]())
    appt = Appointment(
        clinic_id="default",
        patient_id=patient_id,
        provider_id=provider_id,
        service_id=service_id,
        start_time=datetime(2026, 6, 1, 10, 0),
        end_time=datetime(2026, 6, 1, 10, 30),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint=chief_complaint,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt.id


# ---------------------------------------------------------------------------
# 1. chief_complaint persists through v2
# ---------------------------------------------------------------------------

def test_chief_complaint_persists(client):
    patient_id = _create_patient(client)
    provider_id, service_id = _seed_provider_and_service(client)

    appt_id = _create_appointment_db(client, patient_id, provider_id, service_id,
                                      chief_complaint="tooth pain")

    r = client.get(f"/api/v2/clinical/appointments/{appt_id}",
                   headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text
    assert r.json().get("chief_complaint") == "tooth pain"


# ---------------------------------------------------------------------------
# 2. treatment_plan_items tooth_number + care_notes
# ---------------------------------------------------------------------------

def test_treatment_plan_item_tooth_number_and_care_notes(client):
    patient_id = _create_patient(client)

    r = client.post("/api/v2/treatment-plans", json={
        "patient_id": patient_id,
        "items": [
            {
                "procedure_code": "04341",
                "description": "Perio scaling",
                "fee": 250.0,
                "tooth_number": 14,
                "care_notes": "root canal candidate",
            }
        ],
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    plan_id = r.json()["id"]

    r2 = client.get(f"/api/v2/treatment-plans/{plan_id}", headers=CLINIC_HEADERS)
    assert r2.status_code == 200, r2.text
    items = r2.json()["items"]
    assert len(items) == 1
    assert items[0]["tooth_number"] == 14
    assert items[0]["care_notes"] == "root canal candidate"


# ---------------------------------------------------------------------------
# 3. v1 appointment response does NOT leak chief_complaint
# ---------------------------------------------------------------------------

def test_v1_appointment_response_does_NOT_leak_chief_complaint(client):
    patient_id = _create_patient(client)
    provider_id, service_id = _seed_provider_and_service(client)

    appt_id = _create_appointment_db(client, patient_id, provider_id, service_id,
                                      chief_complaint="gum pain")

    r = client.get(f"/api/appointments/{appt_id}", headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text
    assert "chief_complaint" not in r.json()


# ---------------------------------------------------------------------------
# 4. CRM create lead
# ---------------------------------------------------------------------------

def test_crm_create_lead(client):
    r = client.post("/api/v2/crm/leads", json={
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "5551234567",
        "source": "google_ads",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert "id" in body
    assert body["phone"] == "5551234567"
    assert body["source"] == "google_ads"


# ---------------------------------------------------------------------------
# 5. CRM update lead owner
# ---------------------------------------------------------------------------

def test_crm_update_lead_owner(client):
    r = client.post("/api/v2/crm/leads", json={
        "first_name": "Bob",
        "last_name": "Smith",
        "phone": "5559876543",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    lead_id = r.json()["id"]

    r2 = client.put(f"/api/v2/crm/leads/{lead_id}", json={
        "owner_id": "user-abc",
    }, headers=CLINIC_HEADERS)
    assert r2.status_code in (200, 201), r2.text
    assert r2.json().get("owner_id") == "user-abc"


# ---------------------------------------------------------------------------
# 6. CRM activity create and list
# ---------------------------------------------------------------------------

def test_crm_activity_create_and_list(client):
    r = client.post("/api/v2/crm/leads", json={
        "first_name": "Alice",
        "last_name": "Wonder",
        "phone": "5550000001",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    lead_id = r.json()["id"]

    r2 = client.post(f"/api/v2/crm/leads/{lead_id}/activities", json={
        "kind": "note",
        "body": "Called patient, left voicemail.",
    }, headers=CLINIC_HEADERS)
    assert r2.status_code in (200, 201), r2.text
    act = r2.json()
    assert act["kind"] == "note"
    assert "id" in act

    r3 = client.get(f"/api/v2/crm/leads/{lead_id}/activities", headers=CLINIC_HEADERS)
    assert r3.status_code == 200, r3.text
    activities = r3.json()
    assert len(activities) == 1
    assert activities[0]["kind"] == "note"


# ---------------------------------------------------------------------------
# 7. send_whatsapp uses whatsapp: prefix
# ---------------------------------------------------------------------------

def test_send_whatsapp_uses_whatsapp_prefix(monkeypatch):
    calls = []

    class FakeMessages:
        def create(self, **kwargs):
            calls.append(kwargs)
            return type("Msg", (), {"sid": "SM123"})()

    class FakeClient:
        messages = FakeMessages()

    import os
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15550000000")
    monkeypatch.delenv("TWILIO_WHATSAPP_FROM", raising=False)

    import clients.sms_client as sms
    monkeypatch.setattr(sms, "SEND_BOOKING_SMS", True)

    import twilio.rest
    monkeypatch.setattr(twilio.rest, "Client", lambda sid, token: FakeClient())

    sms.send_whatsapp(to="+15551234567", body="hi")
    assert len(calls) == 1
    assert calls[0]["from_"].startswith("whatsapp:")
    assert calls[0]["to"] == "whatsapp:+15551234567"


# ---------------------------------------------------------------------------
# 8. send_communication channel=whatsapp routes to send_whatsapp
# ---------------------------------------------------------------------------

def test_send_communication_channel_whatsapp_routes_to_send_whatsapp(client, monkeypatch):
    patient_id = _create_patient(client)

    called = {}

    def fake_send_whatsapp(to: str, body: str):
        called["to"] = to
        called["body"] = body
        return {"sid": "WA123"}

    import api.v2.communications.router as comm_router
    monkeypatch.setattr(comm_router, "send_whatsapp", fake_send_whatsapp)

    r = client.post("/api/v2/communications/send", json={
        "patient_id": patient_id,
        "channel": "whatsapp",
        "body": "Hello via WhatsApp",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    assert "to" in called

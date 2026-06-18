"""Tests for /api/portal/clinics/{cid}/patients (CRM-facing CRUD)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import app
from database.models import Clinic, Patient

client = TestClient(app)


def test_list_empty_clinic(override_portal_user, db_session):
    db_session.add(Clinic(id="empty_test", name="Empty"))
    db_session.commit()
    override_portal_user(clinic_ids=["empty_test"])
    r = client.get("/api/portal/clinics/empty_test/patients")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "next_cursor": None}


def test_create_then_get(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    body = {"first_name": "Jane", "last_name": "Doe", "phone": "+14035550100", "dob": "1980-01-01"}
    r = client.post("/api/portal/clinics/default/patients", json=body)
    assert r.status_code == 201
    pid = r.json()["patient_id"]
    g = client.get(f"/api/portal/clinics/default/patients/{pid}")
    assert g.status_code == 200
    item = g.json()
    assert item["patient_id"] == pid
    assert item["first_name"] == "Jane"
    assert item["phone_e164"] == "+14035550100"
    assert item["lead_status"] == "new"           # default mapping
    assert item["tags"] == []                     # default crm_tags is dict → coerced to []
    assert item["notes"] == ""


def test_list_returns_renamed_fields(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(
        id="pat-renamed", clinic_id="default",
        first_name="R", last_name="N", phone="+14039990000",
        lead_status_crm="contacted",
        crm_tags=["vip", "follow-up"],
        crm_notes="needs Saturday slot",
        last_contact_at=datetime(2026, 5, 27, 14, 0, 0, tzinfo=timezone.utc),
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/patients")
    item = next(x for x in r.json()["items"] if x["patient_id"] == "pat-renamed")
    assert item["phone_e164"] == "+14039990000"
    assert item["lead_status"] == "contacted"
    assert item["tags"] == ["vip", "follow-up"]
    assert item["notes"] == "needs Saturday slot"
    assert item["last_contact_at"] is not None


def test_list_remaps_lead_status_whitelist(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-won", clinic_id="default", lead_status_crm="won"))
    db_session.add(Patient(id="p-archived", clinic_id="default", lead_status_crm="archived"))
    db_session.add(Patient(id="p-unknown", clinic_id="default", lead_status_crm="zzz"))
    db_session.commit()
    items = {i["patient_id"]: i["lead_status"] for i in client.get(
        "/api/portal/clinics/default/patients").json()["items"]}
    assert items["p-won"] == "completed"
    assert items["p-archived"] == "lost"
    assert items["p-unknown"] == "new"


def test_list_coerces_crm_tags_dict_to_empty_list(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    # Patient.crm_tags default is dict {} (server_default="{}")
    db_session.add(Patient(id="p-default-tags", clinic_id="default"))
    db_session.commit()
    item = next(x for x in client.get(
        "/api/portal/clinics/default/patients").json()["items"]
        if x["patient_id"] == "p-default-tags")
    assert item["tags"] == []


def test_list_response_envelope_has_next_cursor_null(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-env", clinic_id="default"))
    db_session.commit()
    body = client.get("/api/portal/clinics/default/patients").json()
    assert body["next_cursor"] is None
    assert "items" in body and "total" in body


def test_patch_patient_accepts_new_field_names(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-patch-new", clinic_id="default"))
    db_session.commit()
    r = client.patch("/api/portal/clinics/default/patients/p-patch-new", json={
        "tags": ["alpha"], "notes": "hi", "lead_status": "contacted",
    })
    assert r.status_code == 200
    item = r.json()
    assert item["tags"] == ["alpha"]
    assert item["notes"] == "hi"
    assert item["lead_status"] == "contacted"


def test_patch_patient_accepts_legacy_field_names(db_session, override_portal_user):
    """One-way cutover compat — legacy field names still work."""
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-patch-legacy", clinic_id="default"))
    db_session.commit()
    r = client.patch("/api/portal/clinics/default/patients/p-patch-legacy", json={
        "crm_tags": ["legacy"], "crm_notes": "old", "lead_status_crm": "contacted",
    })
    assert r.status_code == 200
    item = r.json()
    assert item["tags"] == ["legacy"]
    assert item["notes"] == "old"
    assert item["lead_status"] == "contacted"


def test_patch_rejects_identity_fields(override_portal_user, db_session):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-ident", clinic_id="default"))
    db_session.commit()
    r = client.patch("/api/portal/clinics/default/patients/p-ident", json={
        "first_name": "Should fail",
    })
    assert r.status_code == 422


def test_delete_soft_deletes_via_archived(override_portal_user, db_session):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-del", clinic_id="default"))
    db_session.commit()
    r = client.delete("/api/portal/clinics/default/patients/p-del")
    assert r.status_code == 200
    # 'archived' maps to FE 'lost' via the whitelist
    assert r.json()["lead_status"] == "lost"


def test_patch_rejects_unknown_lead_status(override_portal_user, db_session):
    """Pydantic Literal whitelist 422s out-of-vocabulary values so the column
    never holds garbage that the read path then silently coerces back."""
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-bad-lead", clinic_id="default"))
    db_session.commit()
    r = client.patch("/api/portal/clinics/default/patients/p-bad-lead", json={
        "lead_status": "banana",
    })
    assert r.status_code == 422


def test_post_rejects_unknown_lead_status(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.post("/api/portal/clinics/default/patients", json={
        "first_name": "X", "lead_status": "banana",
    })
    assert r.status_code == 422


def test_patch_rejects_non_list_tags(override_portal_user, db_session):
    """tags is List[Any] — a bare string at the body would be silently stored
    as JSONB string and break the read path. 422 instead."""
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="p-bad-tags", clinic_id="default"))
    db_session.commit()
    r = client.patch("/api/portal/clinics/default/patients/p-bad-tags", json={
        "tags": "not-a-list",
    })
    assert r.status_code == 422

"""Tests for /api/portal/clinics/{cid}/patients (CRM-facing CRUD)."""

from fastapi.testclient import TestClient

from api.main import app
from database.models import Patient

client = TestClient(app)


def test_list_empty_clinic(override_portal_user, db_session):
    # The autouse seed creates the default clinic but no patients.
    # Other tests (Track 1.1 conftest seeds) may insert patients into "default";
    # use a fresh clinic id to assert empty list semantics.
    override_portal_user(clinic_ids=["default"])
    # Filter on a clinic that exists but might have no patients
    from database.models import Clinic
    db_session.add(Clinic(id="empty_test", name="Empty"))
    db_session.commit()
    override_portal_user(clinic_ids=["empty_test"])
    r = client.get("/api/portal/clinics/empty_test/patients")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0}


def test_create_then_get(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    body = {"first_name": "Jane", "last_name": "Doe", "phone": "+14035550100", "dob": "1980-01-01"}
    r = client.post("/api/portal/clinics/default/patients", json=body)
    assert r.status_code == 201
    pid = r.json()["id"]
    r2 = client.get(f"/api/portal/clinics/default/patients/{pid}")
    assert r2.status_code == 200
    assert r2.json()["first_name"] == "Jane"


def test_patch_crm_fields_succeeds(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="pat_t1", clinic_id="default", first_name="Old", phone="+14030000010"))
    db_session.commit()

    r = client.patch(
        "/api/portal/clinics/default/patients/pat_t1",
        json={"crm_notes": "VIP customer", "lead_status_crm": "won"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["crm_notes"] == "VIP customer"
    assert body["lead_status_crm"] == "won"


def test_patch_identity_fields_rejected(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="pat_t2", clinic_id="default", first_name="DoNotChange", phone="+14030000011"))
    db_session.commit()

    # first_name in body should be rejected with 422 (extra="forbid")
    r = client.patch(
        "/api/portal/clinics/default/patients/pat_t2",
        json={"first_name": "Hacker"},
    )
    assert r.status_code == 422
    # Verify it wasn't changed
    db_session.expire_all()
    p = db_session.query(Patient).filter_by(id="pat_t2").first()
    assert p.first_name == "DoNotChange"


def test_soft_delete_archives(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(id="pat_t3", clinic_id="default", first_name="X", phone="+14030000012"))
    db_session.commit()

    r = client.delete("/api/portal/clinics/default/patients/pat_t3")
    assert r.status_code == 200
    db_session.expire_all()
    p = db_session.query(Patient).filter_by(id="pat_t3").first()
    assert p is not None  # not hard-deleted
    assert p.lead_status_crm == "archived"


def test_get_404_for_missing_patient(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/patients/no_such_id")
    assert r.status_code == 404

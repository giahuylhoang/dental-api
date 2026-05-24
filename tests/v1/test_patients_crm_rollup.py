"""Tests for PUT /api/patients/{id}/crm-rollup (v1 receive endpoint)."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.models import Patient

client = TestClient(app)


@pytest.fixture
def _seed_test_patient(db_session):
    db_session.add(Patient(id="pat_test", clinic_id="default", first_name="X", phone="+14030000000"))
    db_session.commit()
    yield


def test_crm_rollup_updates_only_crm_fields(db_session, _seed_test_patient):
    body = {"lead_status_crm": "contacted", "crm_notes": "called back", "last_contact_at": "2026-05-23T10:00:00Z"}
    r = client.put("/api/patients/pat_test/crm-rollup", json=body, headers={"X-Clinic-Id": "default"})
    assert r.status_code == 200
    db_session.expire_all()
    p = db_session.query(Patient).filter_by(id="pat_test").first()
    assert p.lead_status_crm == "contacted"
    assert p.crm_notes == "called back"
    assert p.first_name == "X"


def test_crm_rollup_404_for_unknown_patient():
    r = client.put("/api/patients/missing/crm-rollup", json={"crm_notes": "x"}, headers={"X-Clinic-Id": "default"})
    assert r.status_code == 404


def test_crm_rollup_rejects_identity_fields(db_session, _seed_test_patient):
    r = client.put(
        "/api/patients/pat_test/crm-rollup",
        json={"first_name": "Hacker"},
        headers={"X-Clinic-Id": "default"},
    )
    assert r.status_code == 422
    db_session.expire_all()
    p = db_session.query(Patient).filter_by(id="pat_test").first()
    assert p.first_name == "X"

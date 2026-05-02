"""Patient lifecycle (v1.1) — pending/active workflow + quick-book endpoint."""
import uuid
from datetime import date

from database.models import Patient
from database.clinical.models import PatientConsent, PatientInsurance
from database.v1_1.lifecycle import (
    get_status, set_status, promote_if_complete, is_complete_for_active,
)
from database.v1_1.models import PatientLifecycle


# ---------------------------------------------------------------------------
# Direct helper API
# ---------------------------------------------------------------------------

def test_default_status_is_active_when_no_row(db_session):
    p = Patient(id=str(uuid.uuid4()), clinic_id="default", first_name="A", last_name="B", phone="5550000001")
    db_session.add(p); db_session.commit()
    assert get_status(db_session, p.id) == "active"


def test_set_status_creates_row(db_session):
    p = Patient(id=str(uuid.uuid4()), clinic_id="default", first_name="A", last_name="B", phone="5550000002")
    db_session.add(p); db_session.commit()
    set_status(db_session, p.id, "default", "pending")
    db_session.commit()
    assert get_status(db_session, p.id) == "pending"
    row = db_session.query(PatientLifecycle).filter_by(patient_id=p.id).one()
    assert row.registered_at is None  # not active yet


def test_set_status_active_stamps_registered_at(db_session):
    p = Patient(id=str(uuid.uuid4()), clinic_id="default", first_name="A", last_name="B", phone="5550000003")
    db_session.add(p); db_session.commit()
    set_status(db_session, p.id, "default", "pending")
    db_session.commit()
    set_status(db_session, p.id, "default", "active")
    db_session.commit()
    row = db_session.query(PatientLifecycle).filter_by(patient_id=p.id).one()
    assert row.status == "active"
    assert row.registered_at is not None


def test_promote_no_op_when_data_incomplete(db_session):
    p = Patient(id=str(uuid.uuid4()), clinic_id="default", first_name="Only", last_name="Phone", phone="5550000004")
    db_session.add(p); db_session.commit()
    set_status(db_session, p.id, "default", "pending")
    db_session.commit()

    final = promote_if_complete(db_session, p)
    db_session.commit()
    assert final == "pending"


def test_promote_flips_to_active_when_complete(db_session):
    p = Patient(
        id=str(uuid.uuid4()), clinic_id="default",
        first_name="Full", last_name="Reg", phone="5550000005",
        dob=date(1980, 1, 1), consent_approved=True,
    )
    db_session.add(p); db_session.commit()
    db_session.add(PatientInsurance(
        clinic_id="default", patient_id=p.id, carrier="Manulife",
        policy_number="123", holder_name="Full Reg", is_primary=True,
    ))
    db_session.commit()

    set_status(db_session, p.id, "default", "pending")
    db_session.commit()

    final = promote_if_complete(db_session, p)
    db_session.commit()
    assert final == "active"
    assert is_complete_for_active(db_session, p) is True


# ---------------------------------------------------------------------------
# /api/v2/clinical/patients/quick-book endpoint
# ---------------------------------------------------------------------------

def test_quick_book_creates_pending_patient(client):
    r = client.post("/api/v2/clinical/patients/quick-book",
                    json={"name": "Walk In", "phone": "(555) 010-1010", "source": "phone"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["first_name"] == "Walk"
    assert body["last_name"] == "In"
    assert body["phone"] == "5550101010"   # digits-only normalization
    assert body["is_new"] is True


def test_quick_book_idempotent_on_phone(client):
    a = client.post("/api/v2/clinical/patients/quick-book",
                    json={"name": "Sam Rep", "phone": "5550202020"})
    assert a.status_code == 200
    b = client.post("/api/v2/clinical/patients/quick-book",
                    json={"name": "Different Name", "phone": "5550202020"})
    assert b.status_code == 200
    assert b.json()["patient_id"] == a.json()["patient_id"]
    assert b.json()["is_new"] is False
    # Original name preserved (we don't overwrite on repeat quick-book)
    assert b.json()["first_name"] == "Sam"


def test_status_endpoint_default_active(client):
    """A patient created via the v1 POST /api/patients (no quick-book) reads as 'active'."""
    cr = client.post("/api/patients", json={"first_name": "V1", "last_name": "Patient", "phone": "5550303030"})
    assert cr.status_code == 200
    pid = cr.json()["id"]
    sr = client.get(f"/api/v2/clinical/patients/{pid}/status")
    assert sr.status_code == 200
    assert sr.json()["status"] == "active"


def test_promote_endpoint_no_op_then_flips(client, db_session):
    qb = client.post("/api/v2/clinical/patients/quick-book",
                     json={"name": "Will Promote", "phone": "5550404040"})
    pid = qb.json()["patient_id"]

    # Initial promote: still pending — incomplete data
    r1 = client.post(f"/api/v2/clinical/patients/{pid}/promote")
    assert r1.status_code == 200 and r1.json()["status"] == "pending"

    # Fill in DOB + consent directly via the DB session (the v1 PUT takes a
    # raw dict and doesn't parse the dob string — known v1 limitation).
    p = db_session.query(Patient).filter_by(id=pid).one()
    p.dob = date(1985, 5, 5)
    p.consent_approved = True
    db_session.commit()

    ins = client.post(f"/api/v2/clinical/patients/{pid}/insurance", json={
        "carrier": "Sun Life", "policy_number": "P9", "holder_name": "Will Promote", "is_primary": True,
    })
    assert ins.status_code == 201, ins.text

    r2 = client.post(f"/api/v2/clinical/patients/{pid}/promote")
    assert r2.status_code == 200
    assert r2.json()["status"] == "active"


def test_set_status_explicit(client):
    qb = client.post("/api/v2/clinical/patients/quick-book", json={"name": "X Y", "phone": "5550505050"})
    pid = qb.json()["patient_id"]
    r = client.post(f"/api/v2/clinical/patients/{pid}/status",
                    json={"status": "inactive", "notes": "no-show 3x"})
    assert r.status_code == 200
    assert r.json()["status"] == "inactive"


def test_set_status_rejects_unknown(client):
    qb = client.post("/api/v2/clinical/patients/quick-book", json={"name": "Z", "phone": "5550606060"})
    pid = qb.json()["patient_id"]
    r = client.post(f"/api/v2/clinical/patients/{pid}/status", json={"status": "ALIEN"})
    assert r.status_code == 400


def test_v1_response_unchanged(client):
    """The v1 GET /api/patients/{id} response shape MUST NOT include status."""
    qb = client.post("/api/v2/clinical/patients/quick-book", json={"name": "V1 Shape", "phone": "5550707070"})
    pid = qb.json()["patient_id"]
    r = client.get(f"/api/patients/{pid}")
    assert r.status_code == 200
    keys = set(r.json().keys())
    assert "status" not in keys, f"v1 response leaked status: {keys}"
    # v1 keys: id, first_name, last_name, phone, email
    assert {"id", "first_name", "last_name", "phone", "email"}.issubset(keys)

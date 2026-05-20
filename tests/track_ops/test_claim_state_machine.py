"""Test insurance claim state machine."""
import pytest
from database.models import Patient, DEFAULT_CLINIC_ID
from database.ops.models import Invoice
from decimal import Decimal


def _make_invoice(db):
    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Ins", phone="555")
    db.add(patient)
    db.flush()
    inv = Invoice(
        clinic_id=DEFAULT_CLINIC_ID,
        patient_id=patient.id,
        status="issued",
        subtotal=Decimal("200"),
        gst=Decimal("10"),
        total=Decimal("210"),
        balance=Decimal("210"),
        currency="CAD",
    )
    db.add(inv)
    db.flush()
    return inv


def test_claim_happy_path(client, db_session):
    """draft → submitted → adjudicated → paid."""
    inv = _make_invoice(db_session)
    db_session.commit()

    # Create
    r = client.post("/api/v2/insurance/claims", json={
        "invoice_id": inv.id,
        "carrier": "Sun Life",
        "kind": "claim",
    })
    assert r.status_code == 201
    claim_id = r.json()["id"]
    assert r.json()["status"] == "draft"

    # Submit
    r2 = client.post(f"/api/v2/insurance/claims/{claim_id}/submit")
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"

    # Adjudicate → accepted
    r3 = client.post(f"/api/v2/insurance/claims/{claim_id}/adjudicate", json={
        "paid_amount": 180.0,
        "status": "accepted",
    })
    assert r3.status_code == 200
    assert r3.json()["status"] == "accepted"

    # Mark paid
    r4 = client.post(f"/api/v2/insurance/claims/{claim_id}/mark-paid", json={"paid_amount": 180.0})
    assert r4.status_code == 200
    assert r4.json()["status"] == "paid"


def test_claim_rejected_path(client, db_session):
    """Rejected claim: adjudicate with rejected status."""
    inv = _make_invoice(db_session)
    db_session.commit()

    r = client.post("/api/v2/insurance/claims", json={"invoice_id": inv.id, "carrier": "Manulife", "kind": "claim"})
    claim_id = r.json()["id"]

    client.post(f"/api/v2/insurance/claims/{claim_id}/submit")

    r2 = client.post(f"/api/v2/insurance/claims/{claim_id}/adjudicate", json={
        "paid_amount": 0,
        "status": "rejected",
    })
    assert r2.json()["status"] == "rejected"

    # Cannot mark paid from rejected
    r3 = client.post(f"/api/v2/insurance/claims/{claim_id}/mark-paid", json={"paid_amount": 0})
    assert r3.status_code == 400


def test_cannot_transition_from_paid(client, db_session):
    """Transitions out of paid are rejected."""
    inv = _make_invoice(db_session)
    db_session.commit()

    r = client.post("/api/v2/insurance/claims", json={"invoice_id": inv.id, "carrier": "GWL", "kind": "claim"})
    claim_id = r.json()["id"]

    client.post(f"/api/v2/insurance/claims/{claim_id}/submit")
    client.post(f"/api/v2/insurance/claims/{claim_id}/adjudicate", json={"paid_amount": 200, "status": "accepted"})
    client.post(f"/api/v2/insurance/claims/{claim_id}/mark-paid", json={"paid_amount": 200})

    # Try to submit again from paid
    r2 = client.post(f"/api/v2/insurance/claims/{claim_id}/submit")
    assert r2.status_code == 400


def test_predetermination_claim(client, db_session):
    """Predetermination kind works same as claim."""
    inv = _make_invoice(db_session)
    db_session.commit()

    r = client.post("/api/v2/insurance/claims", json={
        "invoice_id": inv.id,
        "carrier": "Blue Cross",
        "kind": "predetermination",
    })
    assert r.status_code == 201
    assert r.json()["kind"] == "predetermination"

"""Test invoice math: GST 5%, line totals, balance."""
import pytest
from decimal import Decimal
from database.models import Patient, DEFAULT_CLINIC_ID


def test_invoice_math_three_lines(client, db_session):
    """3 lines × varied qty; GST 5%; totals correct."""
    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Math", phone="555")
    db_session.add(patient)
    db_session.commit()

    r = client.post("/api/v2/billing/invoices", json={
        "patient_id": patient.id,
        "lines": [
            {"procedure_code": "71201", "qty": 1, "unit_price": 100.0, "description": "Line 1"},
            {"procedure_code": "71202", "qty": 2, "unit_price": 75.0, "description": "Line 2"},
            {"procedure_code": "71203", "qty": 1, "unit_price": 50.0, "description": "Line 3"},
        ],
        "gst_rate": 0.05,
    })
    assert r.status_code == 201
    data = r.json()

    # subtotal = 100 + 150 + 50 = 300
    assert abs(data["subtotal"] - 300.0) < 0.01
    # gst = 300 * 0.05 = 15
    assert abs(data["gst"] - 15.0) < 0.01
    # total = 315
    assert abs(data["total"] - 315.0) < 0.01
    # balance = total (no payments yet)
    assert abs(data["balance"] - 315.0) < 0.01
    assert data["currency"] == "CAD"
    assert data["status"] == "draft"


def test_invoice_payment_updates_balance(client, db_session):
    """Payment reduces balance; full payment → paid status."""
    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Pay", phone="556")
    db_session.add(patient)
    db_session.commit()

    r = client.post("/api/v2/billing/invoices", json={
        "patient_id": patient.id,
        "lines": [{"qty": 1, "unit_price": 200.0}],
        "gst_rate": 0.05,
    })
    inv_id = r.json()["id"]

    # Issue it
    client.post(f"/api/v2/billing/invoices/{inv_id}/issue")

    # Partial payment
    r2 = client.post(f"/api/v2/billing/invoices/{inv_id}/payments", json={
        "method": "cash", "amount": 100.0
    })
    assert r2.status_code == 201
    assert r2.json()["status"] == "partial"
    assert abs(r2.json()["balance"] - 110.0) < 0.01  # 210 - 100

    # Full payment
    r3 = client.post(f"/api/v2/billing/invoices/{inv_id}/payments", json={
        "method": "card", "amount": 110.0
    })
    assert r3.json()["status"] == "paid"
    assert abs(r3.json()["balance"]) < 0.01


def test_invoice_gst_configurable(client, db_session):
    """gst_rate=0 → no GST."""
    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="NoGST", phone="557")
    db_session.add(patient)
    db_session.commit()

    r = client.post("/api/v2/billing/invoices", json={
        "patient_id": patient.id,
        "lines": [{"qty": 1, "unit_price": 100.0}],
        "gst_rate": 0.0,
    })
    data = r.json()
    assert abs(data["gst"]) < 0.01
    assert abs(data["total"] - 100.0) < 0.01


def test_seed_billing_fixture(seed_billing):
    """seed_billing fixture creates invoice with correct totals."""
    inv = seed_billing["invoice"]
    assert float(inv.subtotal) == 300.0
    assert float(inv.gst) == 15.0
    assert float(inv.total) == 315.0

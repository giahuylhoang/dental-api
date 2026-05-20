"""Tests for v2 endpoint validation - verify 422 on missing required fields."""
import pytest


def test_billing_invoice_missing_patient_id(client):
    """POST /api/v2/billing/invoices returns 422 when patient_id is missing."""
    resp = client.post(
        "/api/v2/billing/invoices",
        json={"lines": [{"unit_price": 100}]},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422


def test_billing_invoice_missing_lines(client):
    """POST /api/v2/billing/invoices returns 422 when lines is missing."""
    resp = client.post(
        "/api/v2/billing/invoices",
        json={"patient_id": "P-123"},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422


def test_insurance_claim_missing_carrier(client):
    """POST /api/v2/insurance/claims returns 422 when carrier is missing."""
    resp = client.post(
        "/api/v2/insurance/claims",
        json={"kind": "standard"},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422


def test_treatment_plan_missing_patient_id(client):
    """POST /api/v2/treatment_plans returns 422 when patient_id is missing."""
    resp = client.post(
        "/api/v2/treatment_plans",
        json={"title": "Test Plan"},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422


def test_lab_case_missing_patient_id(client):
    """POST /api/v2/lab/cases returns 422 when patient_id is missing."""
    resp = client.post(
        "/api/v2/lab/cases",
        json={"item_description": "Crown"},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422


def test_crm_lead_missing_name(client):
    """POST /api/v2/crm/leads returns 422 when name is missing."""
    resp = client.post(
        "/api/v2/crm/leads",
        json={"source": "website"},
        headers={"X-Clinic-Id": "default"},
    )
    assert resp.status_code == 422

"""Test multi-tenant scoping: clinic A cannot read clinic B's data."""
import pytest
from tests.track_clinical.conftest import make_patient

CLINIC_A = "market-mall-denture"
CLINIC_B = "clinic-other"
HEADERS_A = {"X-Clinic-Id": CLINIC_A}
HEADERS_B = {"X-Clinic-Id": CLINIC_B}


def test_patient_scoped_by_clinic(client_market_mall, client_other_clinic):
    """Patient created in clinic A is not visible to clinic B."""
    pid_a = make_patient(client_market_mall, CLINIC_A)

    # Clinic B tries to access clinic A's patient's medical history
    r = client_other_clinic.get(f"/api/v2/clinical/patients/{pid_a}/medical-history",
                                headers=HEADERS_B)
    assert r.status_code == 404


def test_denture_case_scoped_by_clinic(client_market_mall, client_other_clinic):
    pid_a = make_patient(client_market_mall, CLINIC_A)
    r = client_market_mall.post("/api/v2/clinical/denture-cases",
                                json={"patient_id": pid_a, "arch": "upper", "case_type": "complete"},
                                headers=HEADERS_A)
    case_id = r.json()["id"]

    r2 = client_other_clinic.get(f"/api/v2/clinical/denture-cases/{case_id}", headers=HEADERS_B)
    assert r2.status_code == 404


def test_treatment_plan_scoped_by_clinic(client_market_mall, client_other_clinic):
    pid_a = make_patient(client_market_mall, CLINIC_A)
    r = client_market_mall.post("/api/v2/treatment-plans",
                                json={"patient_id": pid_a, "items": [
                                    {"procedure_code": "X", "fee": 100.0, "insurance_coverage_pct": 0.0}
                                ]},
                                headers=HEADERS_A)
    plan_id = r.json()["id"]

    r2 = client_other_clinic.get(f"/api/v2/treatment-plans/{plan_id}", headers=HEADERS_B)
    assert r2.status_code == 404


def test_lab_vendor_scoped_by_clinic(client_market_mall, client_other_clinic):
    r = client_market_mall.post("/api/v2/lab/vendors",
                                json={"name": "Clinic A Lab"},
                                headers=HEADERS_A)
    vendor_id = r.json()["id"]

    # Clinic B lists vendors — should not see clinic A's vendor
    r2 = client_other_clinic.get("/api/v2/lab/vendors", headers=HEADERS_B)
    assert r2.status_code == 200
    assert not any(v["id"] == vendor_id for v in r2.json())


def test_notes_scoped_by_clinic(client_market_mall, client_other_clinic):
    pid_a = make_patient(client_market_mall, CLINIC_A)
    client_market_mall.post("/api/v2/clinical/notes",
                            json={"patient_id": pid_a, "soap_subjective": "Secret"},
                            headers=HEADERS_A)

    # Clinic B lists notes — should be empty
    r = client_other_clinic.get("/api/v2/clinical/notes",
                                params={"patient_id": pid_a}, headers=HEADERS_B)
    assert r.status_code == 200
    assert r.json() == []

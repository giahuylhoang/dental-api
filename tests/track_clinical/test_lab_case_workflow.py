"""Test lab case workflow."""
import pytest
from tests.track_clinical.conftest import make_patient

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}


def _create_denture_case(client, patient_id):
    r = client.post("/api/v2/clinical/denture-cases",
                    json={"patient_id": patient_id, "arch": "upper", "case_type": "complete"},
                    headers=HEADERS)
    assert r.status_code == 201
    return r.json()["id"]


def _create_vendor(client):
    r = client.post("/api/v2/lab/vendors",
                    json={"name": "Test Lab", "sla_days": 7},
                    headers=HEADERS)
    assert r.status_code == 201
    return r.json()["id"]


def _create_lab_case(client, denture_case_id, vendor_id):
    r = client.post("/api/v2/lab/cases",
                    json={"denture_case_id": denture_case_id, "vendor_id": vendor_id, "lab_fee": 500.0},
                    headers=HEADERS)
    assert r.status_code == 201
    return r.json()


def test_send_and_return(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    dc_id = _create_denture_case(client_market_mall, pid)
    v_id = _create_vendor(client_market_mall)
    case = _create_lab_case(client_market_mall, dc_id, v_id)
    assert case["status"] == "draft"

    r = client_market_mall.post(f"/api/v2/lab/cases/{case['id']}/send", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "sent"
    assert r.json()["sent_at"] is not None

    r = client_market_mall.post(f"/api/v2/lab/cases/{case['id']}/return", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "returned"
    assert r.json()["returned_at"] is not None


def test_remake_creates_child_and_marks_parent(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    dc_id = _create_denture_case(client_market_mall, pid)
    v_id = _create_vendor(client_market_mall)
    parent = _create_lab_case(client_market_mall, dc_id, v_id)

    r = client_market_mall.post(f"/api/v2/lab/cases/{parent['id']}/remake",
                                json={"reason": "Wrong shade"},
                                headers=HEADERS)
    assert r.status_code == 201
    child = r.json()
    assert child["remake_of_id"] == parent["id"]
    assert child["status"] == "draft"

    # Verify parent is now "remake"
    r2 = client_market_mall.get("/api/v2/lab/cases", params={"denture_case_id": dc_id}, headers=HEADERS)
    cases = {c["id"]: c for c in r2.json()}
    assert cases[parent["id"]]["status"] == "remake"


def test_list_filter_by_status(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    dc_id = _create_denture_case(client_market_mall, pid)
    v_id = _create_vendor(client_market_mall)
    case = _create_lab_case(client_market_mall, dc_id, v_id)
    client_market_mall.post(f"/api/v2/lab/cases/{case['id']}/send", headers=HEADERS)

    r = client_market_mall.get("/api/v2/lab/cases", params={"status": "sent"}, headers=HEADERS)
    assert r.status_code == 200
    assert any(c["id"] == case["id"] for c in r.json())

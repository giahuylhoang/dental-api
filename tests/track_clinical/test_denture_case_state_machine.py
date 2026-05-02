"""Test denture case state machine."""
import pytest
from tests.track_clinical.conftest import make_patient

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}


def _create_case(client, patient_id):
    r = client.post("/api/v2/clinical/denture-cases",
                    json={"patient_id": patient_id, "arch": "upper", "case_type": "complete"},
                    headers=HEADERS)
    assert r.status_code == 201, r.text
    return r.json()


def test_initial_stage_is_consult(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    assert case["current_stage"] == "consult"
    assert case["status"] == "open"


def test_valid_forward_transition(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    r = client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                                json={"stage": "prelim_imp"},
                                headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["current_stage"] == "prelim_imp"


def test_skip_stage_rejected(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    # Skip from consult directly to final_imp (skipping prelim_imp)
    r = client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                                json={"stage": "final_imp"},
                                headers=HEADERS)
    assert r.status_code == 400


def test_backward_transition_rejected(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    # Advance to prelim_imp
    client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                            json={"stage": "prelim_imp"}, headers=HEADERS)
    # Try to go back to consult
    r = client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                                json={"stage": "consult"},
                                headers=HEADERS)
    assert r.status_code == 400


def test_closed_case_rejects_advance(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/close", headers=HEADERS)
    r = client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                                json={"stage": "prelim_imp"},
                                headers=HEADERS)
    assert r.status_code == 400


def test_full_stage_progression(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    case = _create_case(client_market_mall, pid)
    stages = ["prelim_imp", "final_imp", "bite_reg", "wax_tryin", "insert", "adjust", "complete"]
    for stage in stages:
        r = client_market_mall.post(f"/api/v2/clinical/denture-cases/{case['id']}/advance",
                                    json={"stage": stage}, headers=HEADERS)
        assert r.status_code == 200, f"Failed at stage {stage}: {r.text}"
        assert r.json()["current_stage"] == stage

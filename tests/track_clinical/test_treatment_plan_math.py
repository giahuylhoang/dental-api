"""Test treatment plan math."""
import pytest
from tests.track_clinical.conftest import make_patient
from database.clinical.models import Procedure

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}


def test_three_item_plan_totals(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    items = [
        {"procedure_code": "51101", "description": "Complete Upper", "fee": 1000.0, "insurance_coverage_pct": 80.0},
        {"procedure_code": "51102", "description": "Complete Lower", "fee": 900.0, "insurance_coverage_pct": 80.0},
        {"procedure_code": "55101", "description": "Adjustment", "fee": 100.0, "insurance_coverage_pct": 50.0},
    ]
    r = client_market_mall.post("/api/v2/treatment-plans",
                                json={"patient_id": pid, "items": items},
                                headers=HEADERS)
    assert r.status_code == 201
    plan = r.json()
    assert plan["total_estimate"] == pytest.approx(2000.0)
    # insurance: 1000*0.8 + 900*0.8 + 100*0.5 = 800 + 720 + 50 = 1570
    assert plan["insurance_estimate"] == pytest.approx(1570.0)
    assert plan["patient_estimate"] == pytest.approx(430.0)
    assert len(plan["items"]) == 3


def test_fee_lookup_from_procedures(client_market_mall, db_session):
    """When fee is omitted, it should be looked up from procedures table."""
    # Seed a procedure
    proc = Procedure(
        clinic_id=CLINIC,
        code="99999",
        name="Test Procedure",
        default_fee=250.0,
        category="other",
    )
    db_session.add(proc)
    db_session.commit()

    pid = make_patient(client_market_mall, CLINIC)
    r = client_market_mall.post("/api/v2/treatment-plans",
                                json={"patient_id": pid, "items": [
                                    {"procedure_code": "99999", "insurance_coverage_pct": 0.0}
                                ]},
                                headers=HEADERS)
    assert r.status_code == 201
    plan = r.json()
    assert plan["total_estimate"] == pytest.approx(250.0)
    assert plan["items"][0]["description"] == "Test Procedure"


def test_replace_items_recomputes_totals(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    r = client_market_mall.post("/api/v2/treatment-plans",
                                json={"patient_id": pid, "items": [
                                    {"procedure_code": "A", "fee": 500.0, "insurance_coverage_pct": 0.0}
                                ]},
                                headers=HEADERS)
    plan_id = r.json()["id"]

    r2 = client_market_mall.patch(f"/api/v2/treatment-plans/{plan_id}/items",
                                  json=[
                                      {"procedure_code": "B", "fee": 200.0, "insurance_coverage_pct": 100.0},
                                      {"procedure_code": "C", "fee": 300.0, "insurance_coverage_pct": 50.0},
                                  ],
                                  headers=HEADERS)
    assert r2.status_code == 200
    plan = r2.json()
    assert plan["total_estimate"] == pytest.approx(500.0)
    assert plan["insurance_estimate"] == pytest.approx(350.0)
    assert plan["patient_estimate"] == pytest.approx(150.0)

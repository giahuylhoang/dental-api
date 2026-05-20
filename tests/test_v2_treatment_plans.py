"""Tests for treatment plans v2 API — both hyphenated and underscore paths."""
import pytest


class TestTreatmentPlansPathAlias:
    """Both /api/v2/treatment-plans and /api/v2/treatment_plans should work."""

    @pytest.fixture
    def patient_id(self, client, db_session):
        """Create a patient for treatment plan tests."""
        from database.models import Patient
        p = Patient(id="tp-test-patient", first_name="Test", last_name="Patient", clinic_id="default")
        db_session.add(p)
        db_session.commit()
        return p.id

    def test_list_hyphenated_path(self, client):
        """GET /api/v2/treatment-plans returns 200."""
        resp = client.get("/api/v2/treatment-plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_underscore_path(self, client):
        """GET /api/v2/treatment_plans returns 200."""
        resp = client.get("/api/v2/treatment_plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_hyphenated_path(self, client, patient_id):
        """POST /api/v2/treatment-plans creates a plan."""
        resp = client.post("/api/v2/treatment-plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0120", "fee": 50.0}]
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data
        assert data["patient_id"] == patient_id

    def test_create_underscore_path(self, client, patient_id):
        """POST /api/v2/treatment_plans creates a plan."""
        resp = client.post("/api/v2/treatment_plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0150", "fee": 75.0}]
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data
        assert data["patient_id"] == patient_id

    def test_get_hyphenated_path(self, client, patient_id):
        """GET /api/v2/treatment-plans/{id} returns the plan."""
        # Create first
        create_resp = client.post("/api/v2/treatment-plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0120"}]
        })
        plan_id = create_resp.json()["id"]
        
        # Get via hyphenated path
        resp = client.get(f"/api/v2/treatment-plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == plan_id

    def test_get_underscore_path(self, client, patient_id):
        """GET /api/v2/treatment_plans/{id} returns the plan."""
        # Create first
        create_resp = client.post("/api/v2/treatment_plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0120"}]
        })
        plan_id = create_resp.json()["id"]
        
        # Get via underscore path
        resp = client.get(f"/api/v2/treatment_plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == plan_id

    def test_present_accept_decline_complete_underscore(self, client, patient_id):
        """Lifecycle actions work on underscore path."""
        # Create
        create_resp = client.post("/api/v2/treatment_plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0120"}]
        })
        plan_id = create_resp.json()["id"]
        
        # Present
        resp = client.post(f"/api/v2/treatment_plans/{plan_id}/present")
        assert resp.status_code == 200
        assert resp.json()["status"] == "presented"
        
        # Accept
        resp = client.post(f"/api/v2/treatment_plans/{plan_id}/accept")
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"
        
        # Complete
        resp = client.post(f"/api/v2/treatment_plans/{plan_id}/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_items_patch_underscore(self, client, patient_id):
        """PATCH /api/v2/treatment_plans/{id}/items works."""
        # Create
        create_resp = client.post("/api/v2/treatment_plans", json={
            "patient_id": patient_id,
            "items": [{"procedure_code": "D0120"}]
        })
        plan_id = create_resp.json()["id"]
        
        # Replace items via patch (endpoint expects List[PlanItemIn] directly)
        resp = client.patch(f"/api/v2/treatment_plans/{plan_id}/items", json=[
            {"procedure_code": "D0120", "fee": 50.0},
            {"procedure_code": "D0150", "fee": 100.0}
        ])
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2

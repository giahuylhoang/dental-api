"""
API tests for dental-api endpoints.

Run from dental-api project root:
  .venv/bin/python -m pytest tests/ -v
  # or: pip install -r requirements-dev.txt && pytest tests/ -v
"""
import pytest


# ---------------------------------------------------------------------------
# Health & debug
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/health", "/api/debug/db-info"])
def test_health_and_debug(client, path):
    response = client.get(path)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------

def test_list_doctors_empty(client):
    response = client.get("/api/doctors")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

def test_list_services_empty(client):
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Patients (create_patient, get_patient, list)
# ---------------------------------------------------------------------------

def test_create_patient_and_get(client):
    """Create patient then get by id - ensures write path works (not readonly)."""
    payload = {
        "first_name": "Asim",
        "last_name": "Ahmed",
        "phone": "83682990959",
        "consent_approved": True,
    }
    create_resp = client.post("/api/patients", json=payload)
    assert create_resp.status_code == 200, create_resp.text
    data = create_resp.json()
    assert "id" in data
    assert data["first_name"] == "Asim"
    assert data["last_name"] == "Ahmed"
    assert data["phone"] == "83682990959"

    patient_id = data["id"]
    get_resp = client.get(f"/api/patients/{patient_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == patient_id
    assert get_resp.json()["first_name"] == "Asim"


def test_get_patient_404(client):
    response = client.get("/api/patients/non-existent-id")
    assert response.status_code == 404


def test_list_patients_by_phone(client):
    client.post(
        "/api/patients",
        json={"first_name": "A", "last_name": "B", "phone": "5551234567"},
    )
    response = client.get("/api/patients", params={"phone": "5551234567"})
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["phone"] == "5551234567"


def test_create_patient_minimal(client):
    """Minimal payload: only required fields for agent-style create."""
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "4031112233",
        "consent_approved": True,
    }
    resp = client.post("/api/patients", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Jane"
    assert body["last_name"] == "Doe"
    assert body["phone"] == "4031112233"
    assert body["id"] is not None

"""Tests for POST /api/clinics/by-spec — admin-token auth + idempotent upsert."""
import pytest


TOKEN = "test-token-abc"


@pytest.fixture(autouse=True)
def _set_token(monkeypatch):
    monkeypatch.setenv("DENTAL_ADMIN_TOKEN", TOKEN)


def test_missing_token_returns_401(client):
    r = client.post("/api/clinics/by-spec", json={"id": "x", "name": "y"})
    assert r.status_code == 401


def test_wrong_token_returns_401(client):
    r = client.post(
        "/api/clinics/by-spec",
        json={"id": "x", "name": "y"},
        headers={"X-Admin-Token": "wrong"},
    )
    assert r.status_code == 401


def test_valid_token_inserts_clinic(client):
    cid = "pytest-clinic"
    r = client.post(
        "/api/clinics/by-spec",
        json={
            "id": cid,
            "name": "Pytest Clinic",
            "timezone": "America/Edmonton",
            "working_hour_start": 9,
            "working_hour_end": 17,
        },
        headers={"X-Admin-Token": TOKEN},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == cid
    assert body["name"] == "Pytest Clinic"
    assert body["timezone"] == "America/Edmonton"


def test_idempotent_second_call_updates_in_place(client):
    cid = "pytest-clinic"
    r1 = client.post(
        "/api/clinics/by-spec",
        json={"id": cid, "name": "Original"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r1.status_code == 200, r1.text
    r2 = client.post(
        "/api/clinics/by-spec",
        json={"id": cid, "name": "Updated"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["name"] == "Updated"


def test_partial_update_preserves_existing_fields(client):
    cid = "pytest-clinic"
    r1 = client.post(
        "/api/clinics/by-spec",
        json={"id": cid, "name": "Init", "address": "111 Main"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r1.status_code == 200, r1.text
    r2 = client.post(
        "/api/clinics/by-spec",
        json={"id": cid, "name": "Init2"},  # address NOT sent
        headers={"X-Admin-Token": TOKEN},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["address"] == "111 Main"


def test_extra_fields_rejected(client):
    r = client.post(
        "/api/clinics/by-spec",
        json={"id": "x", "name": "y", "bogus": 1},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r.status_code == 422

"""V1 regression test: assert all v1 endpoints still work correctly."""
import pytest


def test_v1_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_v1_calendar_slots(client_market_mall):
    r = client_market_mall.get(
        "/api/calendar/slots",
        params={
            "start_datetime": "2026-06-01T09:00:00",
            "end_datetime": "2026-06-01T17:00:00",
        },
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert r.status_code == 200
    data = r.json()
    # Response shape: {"providers": [...]} or {"slots": [...]} — just check 200
    assert isinstance(data, dict)


def test_v1_patients_list(client):
    r = client.get("/api/patients")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_v1_doctors_list(client_market_mall):
    r = client_market_mall.get("/api/providers", headers={"X-Clinic-Id": "market-mall-denture"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_v1_services_list(client):
    r = client.get("/api/services")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_v1_appointments_list(client):
    r = client.get("/api/appointments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_v1_leads_list(client):
    r = client.get("/api/leads")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

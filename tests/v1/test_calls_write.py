"""Tests for POST /api/calls (v1 receive endpoint)."""

from fastapi.testclient import TestClient

from api.main import app
from database.models import CallLog

client = TestClient(app)


def test_post_call_inserts(db_session):
    body = {
        "id": "call_test_1",
        "caller_phone": "+14035550100",
        "started_at": "2026-05-23T10:00:00Z",
        "ended_at": "2026-05-23T10:03:00Z",
        "duration_sec": 180,
        "outcome": "booked",
        "metadata": {"agent": "v3"},
    }
    r = client.post("/api/calls", json=body, headers={"X-Clinic-Id": "default"})
    assert r.status_code in (200, 201)
    row = db_session.query(CallLog).filter_by(id="call_test_1").first()
    assert row is not None
    assert row.outcome == "booked"


def test_post_call_upsert_on_duplicate(db_session):
    body = {"id": "call_dup", "started_at": "2026-05-23T10:00:00Z", "outcome": "first"}
    r1 = client.post("/api/calls", json=body, headers={"X-Clinic-Id": "default"})
    assert r1.status_code in (200, 201)
    # Second call with different outcome should update
    body["outcome"] = "second"
    r2 = client.post("/api/calls", json=body, headers={"X-Clinic-Id": "default"})
    assert r2.status_code in (200, 201)
    row = db_session.query(CallLog).filter_by(id="call_dup").first()
    assert row.outcome == "second"

"""Tests for /api/portal/clinics/{cid}/calls (read-only)."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.portal.calls import _normalize_outcome
from database.models import CallLog

client = TestClient(app)


@pytest.mark.parametrize("stored,expected", [
    # Canonical outcomes pass through unchanged
    ("booked", "booked"),
    ("agent_handled", "agent_handled"),
    ("transferred", "transferred"),
    ("voicemail", "voicemail"),
    ("missed", "missed"),
    ("error", "error"),
    # routing_gate_* prefix passthrough (forward-compat)
    ("routing_gate_transfer", "routing_gate_transfer"),
    ("routing_gate_hangup", "routing_gate_hangup"),
    ("routing_gate_anything_new", "routing_gate_anything_new"),
    # Legacy phase names → agent_handled (uniform remap)
    ("greeting_triage", "agent_handled"),
    ("ended", "agent_handled"),
    ("cancel", "agent_handled"),
    ("closure", "agent_handled"),
    ("verification", "agent_handled"),
    ("intake", "agent_handled"),
    ("anything_unrecognized", "agent_handled"),
    # None → agent_handled
    (None, "agent_handled"),
])
def test_normalize_outcome(stored, expected):
    assert _normalize_outcome(stored) == expected


def test_list_calls_empty(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/calls")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0}


def test_list_calls_with_data(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_1", clinic_id="default", caller_phone="+14035550100",
        started_at=datetime.now(timezone.utc), outcome="booked",
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "call_1"
    assert body["items"][0]["outcome"] == "booked"


def test_get_one_call(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(id="call_2", clinic_id="default", started_at=datetime.now(timezone.utc)))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_2")
    assert r.status_code == 200
    assert r.json()["id"] == "call_2"


def test_get_one_call_404(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/calls/missing")
    assert r.status_code == 404


def test_list_calls_paginates(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    for i in range(5):
        db_session.add(CallLog(id=f"call_p{i}", clinic_id="default", started_at=datetime.now(timezone.utc)))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls?limit=2&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2

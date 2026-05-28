"""Tests for /api/portal/clinics/{cid}/calls (read-only)."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.portal.calls import _is_after_hours, _normalize_outcome, _project_turn
from database.models import CallLog, Clinic

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
    assert r.json() == {"items": [], "total": 0, "next_cursor": None}


def test_list_calls_returns_renamed_fields(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_renamed", clinic_id="default",
        caller_phone="+14035550100",
        started_at=datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc),
        duration_sec=92,
        outcome="booked",
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["call_id"] == "call_renamed"
    assert item["caller_e164"] == "+14035550100"
    assert item["duration_seconds"] == 92
    assert item["outcome"] == "booked"


def test_list_calls_remaps_legacy_outcome(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_legacy_outcome", clinic_id="default",
        started_at=datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc),
        outcome="greeting_triage",
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls")
    item = r.json()["items"][0]
    assert item["outcome"] == "agent_handled"


def test_list_calls_includes_caller_name_from_patient_join(db_session, override_portal_user):
    from database.models import Patient
    override_portal_user(clinic_ids=["default"])
    db_session.add(Patient(
        id="pat-1", clinic_id="default",
        first_name="Jane", last_name="Doe", phone="+14035550100",
    ))
    db_session.add(CallLog(
        id="call_join", clinic_id="default", patient_id="pat-1",
        caller_phone="+14035550100",
        started_at=datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc),
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls")
    item = r.json()["items"][0]
    assert item["caller_name"] == "Jane Doe"
    assert item["patient_id"] == "pat-1"


def test_list_calls_response_has_next_cursor_null(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(id="c1", clinic_id="default",
                           started_at=datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc)))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls")
    assert r.json()["next_cursor"] is None


def test_get_one_call(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(id="call_2", clinic_id="default",
                           started_at=datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc)))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_2")
    assert r.status_code == 200
    # Task 5 rewrites get_call to return call_id; for now accept either key.
    body = r.json()
    assert body.get("call_id", body.get("id")) == "call_2"


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


def test_project_turn_assistant_to_agent_speaker():
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "05:41:28", "role": "assistant", "text": "hi there"}
    out = _project_turn(turn, started)
    assert out["speaker"] == "agent"
    assert out["text"] == "hi there"
    assert out["t"] == 28_000  # 28 seconds × 1000ms
    assert out["confidence"] == 1.0
    assert out["intents"] == []
    assert out["latency_ms"] == {"stt": 0, "llm": 0, "tool": 0, "tts": 0, "total": 0}


def test_project_turn_user_to_caller_speaker():
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "05:41:35", "role": "user", "text": "I want to book"}
    out = _project_turn(turn, started)
    assert out["speaker"] == "caller"
    assert out["t"] == 35_000


def test_project_turn_malformed_ts_defaults_to_zero():
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "not-a-timestamp", "role": "user", "text": "x"}
    out = _project_turn(turn, started)
    assert out["t"] == 0


def test_project_turn_missing_text_returns_empty_string():
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "05:41:00", "role": "user"}
    out = _project_turn(turn, started)
    assert out["text"] == ""


def test_project_turn_passes_through_real_confidence_intents_latency():
    """When the agent later emits rich fields, projection passes them through."""
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {
        "ts": "05:41:10", "role": "user", "text": "x",
        "confidence": 0.42,
        "intents": [{"name": "booking", "score": 0.9}],
        "latency_ms": {"stt": 120, "llm": 300, "tool": 0, "tts": 80, "total": 500},
    }
    out = _project_turn(turn, started)
    assert out["confidence"] == 0.42
    assert out["intents"] == [{"name": "booking", "score": 0.9}]
    assert out["latency_ms"]["total"] == 500


def test_project_turn_midnight_rollover_does_not_collapse_to_zero():
    """A call that starts 23:58 and has a turn at 00:03 must place that turn
    ~5 minutes after start, not back at t=0 (which would happen if we kept
    the same date and clamped with max(0, ...))."""
    started = datetime(2026, 5, 28, 23, 58, 0, tzinfo=timezone.utc)
    turn = {"ts": "00:03:00", "role": "user", "text": "x"}
    out = _project_turn(turn, started)
    assert out["t"] == 5 * 60 * 1000  # 5 minutes after start


def test_project_turn_partial_latency_merges_with_defaults():
    """A partial latency dict (e.g. just stt) must be merged into defaults so
    downstream readers can always rely on all 5 keys being present."""
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "05:41:00", "role": "user", "text": "x",
            "latency_ms": {"stt": 100}}
    out = _project_turn(turn, started)
    assert out["latency_ms"] == {
        "stt": 100, "llm": 0, "tool": 0, "tts": 0, "total": 0,
    }


def test_project_turn_fractional_seconds_parse_to_whole_second():
    """A timestamp with milliseconds like '05:41:28.123' must not collapse
    the whole turn to t=0; sub-second precision is dropped."""
    started = datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc)
    turn = {"ts": "05:41:28.123", "role": "user", "text": "x"}
    out = _project_turn(turn, started)
    assert out["t"] == 28_000


def _clinic(tz="America/Edmonton", start=9, end=17):
    return Clinic(
        id="x", name="X", timezone=tz,
        working_hour_start=start, working_hour_end=end,
    )


def test_is_after_hours_inside_business_hours_false():
    # 18:00 UTC = 12:00 local (Edmonton is UTC-6 in DST). Inside 9–17.
    started = datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc)
    assert _is_after_hours(started, _clinic()) is False


def test_is_after_hours_outside_business_hours_true():
    # 04:00 UTC = 22:00 previous day local. Outside 9–17.
    started = datetime(2026, 5, 28, 4, 0, 0, tzinfo=timezone.utc)
    assert _is_after_hours(started, _clinic()) is True


def test_is_after_hours_no_clinic_returns_false():
    started = datetime(2026, 5, 28, 4, 0, 0, tzinfo=timezone.utc)
    assert _is_after_hours(started, None) is False


def test_is_after_hours_no_started_at_returns_false():
    assert _is_after_hours(None, _clinic()) is False


def test_is_after_hours_missing_working_hours_returns_false():
    c = _clinic()
    c.working_hour_start = None
    started = datetime(2026, 5, 28, 4, 0, 0, tzinfo=timezone.utc)
    assert _is_after_hours(started, c) is False


def test_is_after_hours_invalid_timezone_falls_back_to_edmonton():
    c = _clinic(tz="Not/A_Real_Zone")
    started = datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc)
    # Should not raise; falls back to America/Edmonton (12:00 local → False)
    assert _is_after_hours(started, c) is False


def test_is_after_hours_invalid_timezone_logs_warning(caplog):
    """Silent fallback to Edmonton would mask a clinic mis-configuration —
    confirm we emit a warn log so ops sees it."""
    import logging
    c = _clinic(tz="Not/A_Real_Zone")
    started = datetime(2026, 5, 28, 18, 0, 0, tzinfo=timezone.utc)
    with caplog.at_level(logging.WARNING, logger="api.portal.calls"):
        _is_after_hours(started, c)
    assert any("invalid timezone" in record.message for record in caplog.records)


def test_is_after_hours_naive_datetime_treated_as_utc():
    """CallLog.started_at can come back from the DB naive on SQLite/legacy PG.
    astimezone() on a naive datetime would use system-local time, producing
    a wrong answer in any non-UTC dev environment. Confirm naive inputs are
    treated as UTC."""
    naive = datetime(2026, 5, 28, 18, 0, 0)  # would be 12:00 if interpreted as UTC
    # Same wall-clock value as the UTC-aware version of the inside-hours test,
    # which we know returns False. Naive must produce the same result.
    assert _is_after_hours(naive, _clinic()) is False


def test_get_call_returns_renamed_fields_and_rich_transcript(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_detail", clinic_id="default",
        caller_phone="+14035550100",
        started_at=datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc),
        duration_sec=28,
        outcome="ended",
        transcript=[
            {"ts": "05:41:00", "role": "assistant", "text": "Hi"},
            {"ts": "05:41:05", "role": "user", "text": "I want to book"},
        ],
        call_metadata={"job_id": "AJ_abc", "agent_version": "v3"},
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_detail")
    assert r.status_code == 200
    body = r.json()
    assert body["call_id"] == "call_detail"
    assert body["caller_e164"] == "+14035550100"
    assert body["duration_seconds"] == 28
    assert body["outcome"] == "agent_handled"           # "ended" → remapped
    assert body["job_id"] == "AJ_abc"
    assert body["transcript_turns"] == 2
    assert body["transcript"] == []                     # legacy field, UI ignores
    assert body["rich_transcript"][0]["speaker"] == "agent"
    assert body["rich_transcript"][1]["speaker"] == "caller"
    assert body["rich_transcript"][1]["t"] == 5000
    assert body["logs"] == []
    assert body["intents"] == []
    assert body["errors"] == []
    assert body["flow_path"] == []                      # no metadata.phase_history


def test_get_call_surfaces_flow_path_from_metadata(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_phases", clinic_id="default",
        started_at=datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc),
        call_metadata={
            "phase_history": ["greeting_triage", "intake", "booking"],
        },
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_phases")
    assert r.json()["flow_path"] == ["greeting_triage", "intake", "booking"]


def test_get_call_enriches_appointment_when_metadata_appointment_id_resolves(
    db_session, override_portal_user,
):
    from database.models import Provider, Appointment, Patient
    override_portal_user(clinic_ids=["default"])
    db_session.add(Provider(id=1, clinic_id="default", name="Smith", title="Dr"))
    db_session.add(Patient(id="pat-9", clinic_id="default", first_name="Joe", last_name="K"))
    db_session.add(Appointment(
        id="appt-99", clinic_id="default", patient_id="pat-9", provider_id=1,
        start_time=datetime(2026, 5, 30, 14, 0, 0),
        end_time=datetime(2026, 5, 30, 15, 0, 0),
    ))
    db_session.add(CallLog(
        id="call_appt", clinic_id="default", patient_id="pat-9",
        started_at=datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc),
        outcome="booked",
        call_metadata={"appointment_id": "appt-99"},
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_appt")
    body = r.json()
    assert body["appointment"]["id"] == "appt-99"
    assert body["appointment"]["patient_id"] == "pat-9"
    assert body["patient"]["patient_id"] == "pat-9"
    assert body["patient"]["first_name"] == "Joe"


def test_get_call_appointment_null_when_metadata_missing(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(
        id="call_no_appt", clinic_id="default",
        started_at=datetime(2026, 5, 28, 5, 41, 0, tzinfo=timezone.utc),
    ))
    db_session.commit()
    r = client.get("/api/portal/clinics/default/calls/call_no_appt")
    body = r.json()
    assert body["appointment"] is None
    assert body["patient"] is None

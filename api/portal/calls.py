"""GET /api/portal/clinics/{cid}/calls + GET /{call_id} — read-only call log."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_log = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import CallLog, Clinic

router = APIRouter()


# ── Outcome remap ──────────────────────────────────────────────────────
# Schema doc (packages/shared/schemas/call_record.py:77) enumerates the
# canonical outcomes. Legacy rows wrote phase names instead of dispositions.
# Anything not in the canonical set → 'agent_handled' (uniform remap per
# 2026-05-28-call-log-shape-fix-design §1).
_CANONICAL_OUTCOMES = frozenset({
    "booked", "agent_handled", "transferred", "voicemail", "missed",
    "routing_gate_transfer", "routing_gate_hangup", "error",
})


def _normalize_outcome(raw: Optional[str]) -> str:
    if raw is None:
        return "agent_handled"
    if raw in _CANONICAL_OUTCOMES:
        return raw
    if raw.startswith("routing_gate"):  # forward-compat for new gate variants
        return raw
    return "agent_handled"


# ── Transcript projection ──────────────────────────────────────────────
# Stored shape (legacy):   {ts: "HH:MM:SS", role: "assistant"|"user", text: str}
# Returned shape (rich):   {t: ms_from_call_start, speaker: "agent"|"caller",
#                           text, confidence, intents, latency_ms}
#
# When the agent later emits real confidence/intents/latency on each turn,
# this helper passes them through unchanged.

_LATENCY_DEFAULTS = {"stt": 0, "llm": 0, "tool": 0, "tts": 0, "total": 0}


def _project_turn(turn: Dict[str, Any], started_at: datetime) -> Dict[str, Any]:
    role = turn.get("role")
    speaker = "agent" if role == "assistant" else "caller"
    t_ms = 0
    ts = turn.get("ts")
    if isinstance(ts, str) and ":" in ts:
        try:
            h, m, s = ts.split(":")
            # Drop sub-second portion if present (e.g. "28.123" → 28) so a
            # millisecond timestamp doesn't collapse the whole turn to t=0.
            wall = started_at.replace(
                hour=int(h), minute=int(m), second=int(s.split(".")[0]),
            )
            # Roll forward a day when the turn's wall-clock is before
            # started_at — happens for calls that span midnight.
            if wall < started_at:
                wall += timedelta(days=1)
            t_ms = max(0, int((wall - started_at).total_seconds() * 1000))
        except (ValueError, AttributeError):
            t_ms = 0
    # Merge any partial latency_ms dict into defaults so downstream
    # readers (UI) can rely on all 5 keys being present.
    latency = {**_LATENCY_DEFAULTS, **(turn.get("latency_ms") or {})}
    return {
        "t": t_ms,
        "speaker": speaker,
        "text": turn.get("text") or turn.get("content") or "",
        "confidence": turn.get("confidence", 1.0),
        "intents": turn.get("intents", []),
        "latency_ms": latency,
    }


# ── After-hours computation ────────────────────────────────────────────
# Compares the call's start (UTC) against the clinic's working hours in
# the clinic-local timezone. All "fall back to safe defaults" cases return
# False — the goal is informational, not load-bearing.

def _is_after_hours(started_at: Optional[datetime], clinic: Optional["Clinic"]) -> bool:
    if not started_at or clinic is None:
        return False
    start = clinic.working_hour_start
    end = clinic.working_hour_end
    if start is None or end is None:
        return False
    # CallLog.started_at column is DateTime(timezone=True) but default=datetime.utcnow
    # writes naive values; SQLite has no tz storage. astimezone on a naive datetime
    # treats it as system-local — wrong in dev environments. Coerce to UTC first.
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    tz_name = clinic.timezone or "America/Edmonton"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        _log.warning(
            "clinic %s has invalid timezone %r; falling back to America/Edmonton",
            getattr(clinic, "id", "?"), tz_name,
        )
        tz = ZoneInfo("America/Edmonton")
    local = started_at.astimezone(tz)
    return not (start <= local.hour < end)


class CallLogOut(BaseModel):
    id: str
    clinic_id: str
    caller_phone: Optional[str] = None
    patient_id: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_sec: Optional[int] = None
    outcome: Optional[str] = None
    transcript: Optional[Any] = None
    audio_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @classmethod
    def from_row(cls, row: CallLog) -> "CallLogOut":
        return cls(
            id=row.id,
            clinic_id=row.clinic_id,
            caller_phone=row.caller_phone,
            patient_id=row.patient_id,
            started_at=row.started_at.isoformat() if row.started_at else None,
            ended_at=row.ended_at.isoformat() if row.ended_at else None,
            duration_sec=row.duration_sec,
            outcome=row.outcome,
            transcript=row.transcript,
            audio_url=row.audio_url,
            metadata=row.call_metadata or {},
        )


class ListCallsResponse(BaseModel):
    items: List[CallLogOut]
    total: int


@router.get("", response_model=ListCallsResponse)
def list_calls(
    clinic_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ListCallsResponse:
    q = db.query(CallLog).filter_by(clinic_id=clinic_id).order_by(CallLog.started_at.desc())
    total = q.count()
    items = [CallLogOut.from_row(r) for r in q.limit(limit).offset(offset).all()]
    return ListCallsResponse(items=items, total=total)


@router.get("/{call_id}", response_model=CallLogOut)
def get_call(clinic_id: str, call_id: str, db: Session = Depends(get_db)) -> CallLogOut:
    row = db.query(CallLog).filter_by(id=call_id, clinic_id=clinic_id).first()
    if row is None:
        raise HTTPException(404, "call_not_found")
    return CallLogOut.from_row(row)

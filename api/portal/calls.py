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
from database.models import CallLog, Clinic, Patient

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


def _summary_dict(row: CallLog, patient: Optional[Patient], clinic: Optional[Clinic]) -> Dict[str, Any]:
    transcript_arr = row.transcript if isinstance(row.transcript, list) else []
    metadata = row.call_metadata or {}
    name_parts = [patient.first_name, patient.last_name] if patient else []
    name = " ".join(p for p in name_parts if p).strip() or None
    return {
        "call_id": row.id,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "ended_at": row.ended_at.isoformat() if row.ended_at else None,
        "duration_seconds": row.duration_sec,
        "caller_e164": row.caller_phone,
        "caller_name": name,
        "patient_id": row.patient_id,
        "outcome": _normalize_outcome(row.outcome),
        "language": metadata.get("language"),
        "transcript_turns": len(transcript_arr),
        "after_hours": _is_after_hours(row.started_at, clinic),
        "appointment_id": metadata.get("appointment_id"),
    }


@router.get("")
def list_calls(
    clinic_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    base_q = db.query(CallLog).filter(CallLog.clinic_id == clinic_id)
    total = base_q.count()
    # Patient join is scoped to the same clinic_id so a cross-tenant FK
    # (data drift / migration error) cannot leak another clinic's caller
    # name into this response. Project CLAUDE.md requires every query to
    # filter by clinic_id.
    rows = (
        db.query(CallLog, Patient)
          .outerjoin(
              Patient,
              (Patient.id == CallLog.patient_id)
              & (Patient.clinic_id == CallLog.clinic_id),
          )
          .filter(CallLog.clinic_id == clinic_id)
          .order_by(CallLog.started_at.desc())
          .limit(limit).offset(offset).all()
    )
    items = [_summary_dict(row, patient, clinic) for row, patient in rows]
    return {"items": items, "total": total, "next_cursor": None}


@router.get("/{call_id}", response_model=CallLogOut)
def get_call(clinic_id: str, call_id: str, db: Session = Depends(get_db)) -> CallLogOut:
    row = db.query(CallLog).filter_by(id=call_id, clinic_id=clinic_id).first()
    if row is None:
        raise HTTPException(404, "call_not_found")
    return CallLogOut.from_row(row)

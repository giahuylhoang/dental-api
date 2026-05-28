"""GET /api/portal/clinics/{cid}/calls + GET /{call_id} — read-only call log."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import CallLog

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

def _project_turn(turn: Dict[str, Any], started_at: datetime) -> Dict[str, Any]:
    role = turn.get("role")
    speaker = "agent" if role == "assistant" else "caller"
    t_ms = 0
    ts = turn.get("ts")
    if isinstance(ts, str) and ":" in ts:
        try:
            h, m, s = ts.split(":")
            wall = started_at.replace(hour=int(h), minute=int(m), second=int(s))
            t_ms = max(0, int((wall - started_at).total_seconds() * 1000))
        except (ValueError, AttributeError):
            t_ms = 0
    return {
        "t": t_ms,
        "speaker": speaker,
        "text": turn.get("text") or turn.get("content") or "",
        "confidence": turn.get("confidence", 1.0),
        "intents": turn.get("intents", []),
        "latency_ms": turn.get("latency_ms", {
            "stt": 0, "llm": 0, "tool": 0, "tts": 0, "total": 0,
        }),
    }


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

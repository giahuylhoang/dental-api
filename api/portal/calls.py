"""GET /api/portal/clinics/{cid}/calls + GET /{call_id} — read-only call log."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_log = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Appointment, CallLog, Clinic, Patient

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


# AppointmentStatus enum (database/models.py) → frontend AppointmentRecord.status
# union ('booked' | 'cancelled' | 'rescheduled' | 'pending_human_review'). Any
# unknown value defaults to 'booked' so the UI's StatusPill always lights up.
_APPT_STATUS_TO_FE = {
    "SCHEDULED": "booked",
    "CONFIRMED": "booked",
    "REMINDER_SENT": "booked",
    "COMPLETED": "booked",
    "NO_SHOW": "booked",
    "CANCELLED": "cancelled",
    "RESCHEDULED": "rescheduled",
    "PENDING": "pending_human_review",
    "PENDING_SYNC": "pending_human_review",
}


def _project_appointment_status(raw_status: Any) -> str:
    if raw_status is None:
        return "booked"
    key = raw_status.value if hasattr(raw_status, "value") else str(raw_status)
    return _APPT_STATUS_TO_FE.get(key.upper(), "booked")


def _project_appointment(appt: Optional[Appointment], patient: Optional[Patient]) -> Optional[Dict[str, Any]]:
    if appt is None:
        return None
    patient_name = ""
    if patient:
        patient_name = " ".join(p for p in [patient.first_name, patient.last_name] if p).strip()
    return {
        "id": appt.id,
        "patient_id": appt.patient_id,
        "patient_name": patient_name,
        "provider": "",  # provider join deferred — UI tolerates empty
        "time_start": appt.start_time.isoformat() if appt.start_time else None,
        "time_end": appt.end_time.isoformat() if appt.end_time else None,
        "procedure": "",
        "status": _project_appointment_status(appt.status),
        "task": "SCHEDULE",
        "booked_by": "ai",
        "source_call_id": None,
    }


# Patient.lead_status_crm carries CRM-side enum values that don't all align
# with the frontend's LeadStatus union. Whitelist the ones that do; everything
# else defaults to 'new'. 'won' maps to 'completed' which is the closest FE term.
_LEAD_STATUS_TO_FE = {
    "new": "new", "contacted": "contacted", "booked": "booked",
    "completed": "completed", "lost": "lost",
    "won": "completed", "archived": "lost",
}


def _project_patient(patient: Optional[Patient]) -> Optional[Dict[str, Any]]:
    if patient is None:
        return None
    # crm_tags column defaults to {} (dict) but the FE expects a list. Coerce
    # to list when it's already a list, else empty.
    raw_tags = patient.crm_tags
    tags = raw_tags if isinstance(raw_tags, list) else []
    raw_lead = (patient.lead_status_crm or "new").lower()
    return {
        "clinic_id": patient.clinic_id,
        "patient_id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "phone_e164": patient.phone,
        "email": patient.email,
        "dob": patient.dob.isoformat() if patient.dob else None,
        "lead_status": _LEAD_STATUS_TO_FE.get(raw_lead, "new"),
        "tags": tags,
        "notes": patient.crm_notes or "",
        "total_calls": 0,
        "last_call_id": None,
        "last_outcome": None,
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
        # Patient model has no updated_at column today; FE type expects the key
        # so emit null until the schema gains the column.
        "updated_at": None,
        "last_contact_at": patient.last_contact_at.isoformat() if patient.last_contact_at else None,
    }


def _detail_dict(
    row: CallLog,
    patient: Optional[Patient],
    appointment: Optional[Appointment],
    clinic: Optional[Clinic],
) -> Dict[str, Any]:
    summary = _summary_dict(row, patient, clinic)
    transcript_arr = row.transcript if isinstance(row.transcript, list) else []
    metadata = row.call_metadata or {}
    return {
        **summary,
        "room_name": metadata.get("room_name"),
        "job_id": metadata.get("job_id"),
        "transcript": [],
        "rich_transcript": [_project_turn(t, row.started_at) for t in transcript_arr],
        "intents": [],
        "logs": [],
        "flow_path": metadata.get("phase_history") or [],
        "appointment": _project_appointment(appointment, patient),
        "patient": _project_patient(patient),
        "token_usage": metadata.get("token_usage"),
        "metadata": metadata,
        "errors": [],
    }


@router.get("/{call_id}")
def get_call(clinic_id: str, call_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row = db.query(CallLog).filter_by(id=call_id, clinic_id=clinic_id).first()
    if row is None:
        raise HTTPException(404, "call_not_found")
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    patient = None
    if row.patient_id:
        # Scope the patient lookup by clinic_id defensively (multi-tenancy).
        patient = (
            db.query(Patient)
              .filter_by(id=row.patient_id, clinic_id=clinic_id)
              .first()
        )
    appt = None
    appt_id = (row.call_metadata or {}).get("appointment_id")
    if appt_id:
        appt = (
            db.query(Appointment)
              .filter_by(id=appt_id, clinic_id=clinic_id)
              .first()
        )
    return _detail_dict(row, patient, appt, clinic)

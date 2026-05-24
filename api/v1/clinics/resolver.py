"""Server-side merge of clinic config across:

  practice_types  ← clinics columns  ← per-clinic override tables

The merge order is the same one the dental-agent YAML loader has used
forever (base/<practice>.yaml ← product.yaml ← ops.yaml). Centralizing
it here means the agent consumes a flat JSON dict and doesn't need to
know about inheritance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database.models import (
    Clinic,
    ClinicAiDisclosure,
    ClinicAiVoice,
    ClinicClosure,
    ClinicRouting,
    PracticeType,
    Provider,
)


def resolve_clinic_config(db: Session, clinic_id: str) -> Optional[Dict[str, Any]]:
    """Return the fully merged config dict, or None if the clinic doesn't exist."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).one_or_none()
    if clinic is None:
        return None

    pt: Optional[PracticeType] = clinic.practice_type
    voice: Optional[ClinicAiVoice] = db.query(ClinicAiVoice).filter(
        ClinicAiVoice.clinic_id == clinic_id
    ).one_or_none()
    disc: Optional[ClinicAiDisclosure] = db.query(ClinicAiDisclosure).filter(
        ClinicAiDisclosure.clinic_id == clinic_id
    ).one_or_none()

    base_assistant = pt.assistant_name if pt else "Emma"
    base_disc_required = pt.ai_disclosure_required if pt else False
    base_disc_phrase = pt.ai_disclosure_phrase if pt else "I'm an AI assistant"
    base_greeting = pt.greeting_message if pt else ""

    greeting_override = (clinic.greeting or {}).get("message") if clinic.greeting else None

    feature_flags: Dict[str, Any] = dict(pt.default_feature_flags) if pt else {}
    feature_flags.update(clinic.feature_flags_overrides or {})

    providers: List[str] = [
        p.name for p in db.query(Provider).filter(
            Provider.clinic_id == clinic_id,
            Provider.is_active == True,  # noqa: E712 - SQLA prefers explicit ==
        ).order_by(Provider.id).all()
    ]

    return {
        "id": clinic.id,
        "name": clinic.name,
        "display_name": clinic.display_name or clinic.name,
        "timezone": clinic.timezone,
        "address": clinic.address,
        "contact_phone": clinic.contact_phone,
        "practice_type": clinic.practice_type_id,
        "assistant_name": (voice.assistant_name if voice else base_assistant),
        "ai_disclosure_required": (disc.required if disc else base_disc_required),
        "ai_disclosure_phrase": (disc.phrase if disc else base_disc_phrase),
        "greeting_message": greeting_override or base_greeting,
        "triage_questions": (pt.triage_questions if pt else []),
        "pricing_preface": (pt.pricing_preface if pt else None),
        "pricing_dentures_range": (pt.pricing_dentures_range if pt else None),
        "treatment_steps_guardrail": (pt.treatment_steps_guardrail if pt else None),
        "feature_flags": feature_flags,
        "general_consultation_service_id": clinic.general_consultation_service_id,
        "knowledge_base_path": clinic.knowledge_base_path,
        "provider_names": providers,
        "routing": _resolve_routing(db, clinic),
    }


def resolve_clinic_routing(db: Session, clinic_id: str) -> Optional[Dict[str, Any]]:
    """Return only the routing block, or None if the clinic doesn't exist."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).one_or_none()
    if clinic is None:
        return None
    return _resolve_routing(db, clinic)


def _resolve_routing(db: Session, clinic: Clinic) -> Dict[str, Any]:
    routing: Optional[ClinicRouting] = clinic.routing
    holidays: List[str] = [
        _isoformat_date(c.start_date)
        for c in db.query(ClinicClosure).filter(
            ClinicClosure.clinic_id == clinic.id,
            ClinicClosure.kind == "holiday",
        ).order_by(ClinicClosure.start_date).all()
    ]
    if routing is None:
        return {
            "timezone": clinic.timezone,
            "dids": [],
            "front_desk_numbers": [],
            "ring_timeout_seconds": 20,
            "hours": {},
            "holidays": holidays,
            "ai_after_hours": True,
            "ai_in_hours_overflow": True,
            "backup_number": None,
            "ai_sip_uri": None,
        }
    return {
        "timezone": clinic.timezone,
        "dids": list(routing.dids or []),
        "front_desk_numbers": list(routing.front_desk_numbers or []),
        "ring_timeout_seconds": routing.ring_timeout_seconds,
        "hours": dict(routing.hours or {}),
        "holidays": holidays,
        "ai_after_hours": routing.ai_after_hours,
        "ai_in_hours_overflow": routing.ai_in_hours_overflow,
        "backup_number": routing.backup_number,
        "ai_sip_uri": routing.ai_sip_uri,
    }


def resolve_clinic_id_for_did(db: Session, did: str) -> Optional[str]:
    """Reverse-index lookup using the GIN index on clinic_routing.dids."""
    if not did:
        return None
    normalized = _normalize_did(did)
    row = db.query(ClinicRouting).filter(
        ClinicRouting.dids.any(normalized)
    ).first()
    return row.clinic_id if row else None


def _isoformat_date(value) -> str:
    """ClinicClosure.start_date is a python ``date`` on PG, but tests may pass
    a string literal in fixtures — accept both and always emit ISO."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _normalize_did(did: str) -> str:
    """Strip non-digits, keep leading '+'. Mirrors services/routing_webhook/store.py:_normalize_did."""
    s = (did or "").strip()
    plus = "+" if s.startswith("+") else ""
    digits = "".join(c for c in s if c.isdigit())
    return f"{plus}{digits}" if (plus or digits) else ""

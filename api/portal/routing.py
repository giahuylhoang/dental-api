"""GET/PUT /api/portal/clinics/{cid}/routing + POST /preview.

GET projects from ClinicRouting (config) + Clinic.timezone +
ClinicClosure (kind='holiday', single-day) into the admin frontend's
RoutingConfig shape (lib/types.ts:178).

PUT accepts the same shape and writes back to all three sources.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Clinic, ClinicRouting
from database.v1_1.models import ClinicClosure

router = APIRouter()


class RoutingHours(BaseModel):
    open: Optional[str] = None
    close: Optional[str] = None


class RoutingConfigBody(BaseModel):
    timezone: str
    dids: List[str] = []
    front_desk_numbers: List[str] = []
    ring_timeout_seconds: int = 20
    hours: Dict[str, RoutingHours] = {}
    holidays: List[str] = []
    ai_after_hours: bool = True
    ai_in_hours_overflow: bool = True
    backup_number: Optional[str] = None
    ai_sip_uri: Optional[str] = None


class PreviewRequest(BaseModel):
    rules: Dict[str, Any] = {}
    context: Dict[str, Any] = {}


def _serialize_routing(
    config: Optional[ClinicRouting],
    clinic: Optional[Clinic],
    closures: List[ClinicClosure],
) -> Dict[str, Any]:
    """Project the three source tables into the FE's RoutingConfig shape."""
    tz = (clinic.timezone if clinic and clinic.timezone else "America/Edmonton")
    return {
        "timezone": tz,
        "dids": list(config.dids) if config and config.dids else [],
        "front_desk_numbers": (
            list(config.front_desk_numbers) if config and config.front_desk_numbers else []
        ),
        "ring_timeout_seconds": config.ring_timeout_seconds if config else 20,
        "hours": dict(config.hours) if config and config.hours else {},
        "holidays": sorted(c.start_date.isoformat() for c in closures),
        "ai_after_hours": config.ai_after_hours if config else True,
        "ai_in_hours_overflow": config.ai_in_hours_overflow if config else True,
        "backup_number": config.backup_number if config else None,
        "ai_sip_uri": config.ai_sip_uri if config else None,
    }


@router.get("")
def get_routing(clinic_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    config = db.query(ClinicRouting).filter_by(clinic_id=clinic_id).first()
    clinic = db.query(Clinic).filter_by(id=clinic_id).first()
    closures = (
        db.query(ClinicClosure)
        .filter_by(clinic_id=clinic_id, kind="holiday")
        .filter(ClinicClosure.end_date.is_(None))
        .all()
    )
    return _serialize_routing(config, clinic, closures)


@router.put("")
def put_routing(
    clinic_id: str,
    body: RoutingConfigBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # Authorization is enforced by the router-level Depends(require_clinic_access)
    # in api/portal/__init__.py; no need to re-thread the user here.
    # Upsert ClinicRouting
    config = db.query(ClinicRouting).filter_by(clinic_id=clinic_id).first()
    if config is None:
        config = ClinicRouting(clinic_id=clinic_id)
        db.add(config)
    config.dids = list(body.dids)
    config.front_desk_numbers = list(body.front_desk_numbers)
    config.ring_timeout_seconds = body.ring_timeout_seconds
    config.hours = {k: v.model_dump() for k, v in body.hours.items()}
    config.ai_after_hours = body.ai_after_hours
    config.ai_in_hours_overflow = body.ai_in_hours_overflow
    config.backup_number = body.backup_number
    config.ai_sip_uri = body.ai_sip_uri

    # Update Clinic.timezone
    clinic = db.query(Clinic).filter_by(id=clinic_id).first()
    if clinic is not None and body.timezone:
        clinic.timezone = body.timezone

    # Replace single-day holiday closures. De-dup the incoming list so an
    # accidental ["2026-12-25", "2026-12-25"] doesn't insert duplicate rows
    # (the underlying table has no uniqueness constraint).
    db.query(ClinicClosure).filter_by(clinic_id=clinic_id, kind="holiday").filter(
        ClinicClosure.end_date.is_(None)
    ).delete(synchronize_session=False)
    for ymd in set(body.holidays):
        try:
            d = date.fromisoformat(ymd)
        except ValueError:
            continue
        db.add(ClinicClosure(
            clinic_id=clinic_id, start_date=d, kind="holiday",
            reason=None,
        ))

    db.commit()
    # Re-fetch and serialize for the response (round-trip).
    config = db.query(ClinicRouting).filter_by(clinic_id=clinic_id).first()
    closures = (
        db.query(ClinicClosure)
        .filter_by(clinic_id=clinic_id, kind="holiday")
        .filter(ClinicClosure.end_date.is_(None))
        .all()
    )
    return _serialize_routing(config, clinic, closures)


@router.post("/preview")
def preview(clinic_id: str, body: PreviewRequest) -> Dict[str, Any]:
    """Pure-function dry-run of a routing decision. No storage."""
    decision = body.rules.get("default_provider", "front_desk")
    return {"decision": decision, "matched_rule": "default_provider"}

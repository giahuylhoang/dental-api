"""GET/PUT /api/portal/clinics/{cid}/routing + POST /preview."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.portal.deps import PortalUser, get_portal_user
from database.models import ClinicRoutingRules

router = APIRouter()


class RoutingRulesBody(BaseModel):
    rules: Dict[str, Any] = {}


class PreviewRequest(BaseModel):
    rules: Dict[str, Any] = {}
    context: Dict[str, Any] = {}


@router.get("", response_model=RoutingRulesBody)
def get_routing(clinic_id: str, db: Session = Depends(get_db)) -> RoutingRulesBody:
    row = db.query(ClinicRoutingRules).filter_by(clinic_id=clinic_id).first()
    return RoutingRulesBody(rules=(row.rules if row else {}))


@router.put("", response_model=RoutingRulesBody)
def put_routing(
    clinic_id: str,
    body: RoutingRulesBody,
    db: Session = Depends(get_db),
    user: PortalUser = Depends(get_portal_user),
) -> RoutingRulesBody:
    row = db.query(ClinicRoutingRules).filter_by(clinic_id=clinic_id).first()
    if row is None:
        row = ClinicRoutingRules(clinic_id=clinic_id, rules=body.rules, updated_by=user.email)
        db.add(row)
    else:
        row.rules = body.rules
        row.updated_by = user.email
    db.commit()
    db.refresh(row)
    return RoutingRulesBody(rules=row.rules)


@router.post("/preview")
def preview(clinic_id: str, body: PreviewRequest) -> Dict[str, Any]:
    """Pure-function dry-run of a routing decision. No storage."""
    decision = body.rules.get("default_provider", "front_desk")
    return {"decision": decision, "matched_rule": "default_provider"}

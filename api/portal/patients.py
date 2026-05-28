"""CRM-facing CRUD over the patients table.

Returns the admin frontend's PatientRecord shape (lib/types.ts:210). Identity
fields (first_name, last_name, phone, dob) are owned by the agent's
verify_patient + record_patient_info flow and are NOT modifiable via PATCH.
PATCH accepts both legacy column names (lead_status_crm, crm_tags, crm_notes)
and the FE-aligned names (lead_status, tags, notes) for one-way cutover compat.
DELETE is a soft delete — sets lead_status_crm='archived'.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.portal._shared import LEAD_STATUS_TO_FE, LeadStatusInput
from database.models import Patient

router = APIRouter()


# Re-export under the old private name so any external import keeps working.
_LEAD_STATUS_TO_FE = LEAD_STATUS_TO_FE


def _serialize_patient(p: Patient) -> Dict[str, Any]:
    raw_tags = p.crm_tags
    tags = raw_tags if isinstance(raw_tags, list) else []
    raw_lead = (p.lead_status_crm or "new").lower()
    return {
        "clinic_id": p.clinic_id,
        "patient_id": p.id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "phone_e164": p.phone,
        "email": p.email,
        "dob": p.dob.isoformat() if p.dob else None,
        "lead_status": _LEAD_STATUS_TO_FE.get(raw_lead, "new"),
        "tags": tags,
        "notes": p.crm_notes or "",
        "total_calls": 0,
        "last_call_id": None,
        "last_outcome": None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": None,  # no updated_at column on Patient
        "last_contact_at": p.last_contact_at.isoformat() if p.last_contact_at else None,
    }


class PatientCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[str] = None
    # CRM fields accept both legacy and FE-aligned names. lead_status uses
    # the Literal whitelist so out-of-vocabulary values 422 at the Pydantic
    # boundary (otherwise the DB would silently store garbage that reads
    # then coerce back to "new").
    crm_notes: Optional[str] = None
    notes: Optional[str] = None
    lead_status_crm: Optional[LeadStatusInput] = None
    lead_status: Optional[LeadStatusInput] = None


class PatientCRMUpdate(BaseModel):
    """PATCH body — ONLY CRM columns. Identity fields cause 422.

    Accepts BOTH the legacy column names (lead_status_crm, crm_tags, crm_notes)
    and the FE-aligned names (lead_status, tags, notes). When both are given,
    the FE-aligned name wins. lead_status uses the Literal whitelist so
    out-of-vocabulary values 422 at the Pydantic boundary.
    """
    lead_status_crm: Optional[LeadStatusInput] = None
    lead_status: Optional[LeadStatusInput] = None
    crm_tags: Optional[List[Any]] = None
    tags: Optional[List[Any]] = None
    crm_notes: Optional[str] = None
    notes: Optional[str] = None
    last_contact_at: Optional[datetime] = None

    model_config = {"extra": "forbid"}


@router.get("")
def list_patients(
    clinic_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    q = (
        db.query(Patient)
        .filter_by(clinic_id=clinic_id)
        .order_by(Patient.last_contact_at.desc().nullslast())
    )
    total = q.count()
    items = [_serialize_patient(p) for p in q.limit(limit).offset(offset).all()]
    return {"items": items, "total": total, "next_cursor": None}


@router.post("", status_code=201)
def create_patient(
    clinic_id: str, body: PatientCreate, db: Session = Depends(get_db),
) -> Dict[str, Any]:
    p = Patient(
        id=str(uuid.uuid4()), clinic_id=clinic_id,
        first_name=body.first_name, last_name=body.last_name, phone=body.phone,
        dob=body.dob, email=body.email,
        # FE-aligned name wins if both are given.
        crm_notes=body.notes if body.notes is not None else body.crm_notes,
        lead_status_crm=(
            body.lead_status if body.lead_status is not None else body.lead_status_crm
        ),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _serialize_patient(p)


@router.get("/{patient_id}")
def get_patient(
    clinic_id: str, patient_id: str, db: Session = Depends(get_db),
) -> Dict[str, Any]:
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    return _serialize_patient(p)


@router.patch("/{patient_id}")
def patch_patient(
    clinic_id: str, patient_id: str, body: PatientCRMUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    # FE-aligned name wins if both provided.
    if body.lead_status is not None or body.lead_status_crm is not None:
        p.lead_status_crm = (
            body.lead_status if body.lead_status is not None else body.lead_status_crm
        )
    if body.tags is not None or body.crm_tags is not None:
        p.crm_tags = body.tags if body.tags is not None else body.crm_tags
    if body.notes is not None or body.crm_notes is not None:
        p.crm_notes = body.notes if body.notes is not None else body.crm_notes
    if body.last_contact_at is not None:
        p.last_contact_at = body.last_contact_at
    db.commit()
    db.refresh(p)
    return _serialize_patient(p)


@router.delete("/{patient_id}")
def delete_patient(
    clinic_id: str, patient_id: str, db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Soft delete — sets lead_status_crm='archived' to preserve FK integrity."""
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    p.lead_status_crm = "archived"
    db.commit()
    db.refresh(p)
    return _serialize_patient(p)

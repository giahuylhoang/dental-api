"""CRM-facing CRUD over the patients table.

Identity fields (first_name, last_name, phone, dob) are owned by the
agent's verify_patient + record_patient_info flow and are NOT modifiable
via PATCH. PATCH only accepts CRM columns (extra="forbid" enforced).
DELETE is a soft delete — sets lead_status_crm='archived' to preserve
FK integrity from appointments / call_logs.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Patient

router = APIRouter()


class PatientOut(BaseModel):
    id: str
    clinic_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[str] = None
    email: Optional[str] = None
    lead_status_crm: Optional[str] = None
    crm_tags: Dict[str, Any] = {}
    crm_notes: Optional[str] = None
    last_contact_at: Optional[str] = None


def _to_out(p: Patient) -> PatientOut:
    return PatientOut(
        id=p.id, clinic_id=p.clinic_id, first_name=p.first_name, last_name=p.last_name,
        phone=p.phone, dob=p.dob.isoformat() if p.dob else None, email=p.email,
        lead_status_crm=p.lead_status_crm, crm_tags=p.crm_tags or {},
        crm_notes=p.crm_notes,
        last_contact_at=p.last_contact_at.isoformat() if p.last_contact_at else None,
    )


class PatientCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[str] = None
    crm_notes: Optional[str] = None
    lead_status_crm: Optional[str] = None


class PatientCRMUpdate(BaseModel):
    """PATCH body — ONLY CRM columns are accepted. Identity fields cause 422."""
    lead_status_crm: Optional[str] = None
    crm_tags: Optional[Dict[str, Any]] = None
    crm_notes: Optional[str] = None
    last_contact_at: Optional[datetime] = None

    model_config = {"extra": "forbid"}


class ListPatientsResponse(BaseModel):
    items: List[PatientOut]
    total: int


@router.get("", response_model=ListPatientsResponse)
def list_patients(
    clinic_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ListPatientsResponse:
    q = (
        db.query(Patient)
        .filter_by(clinic_id=clinic_id)
        .order_by(Patient.last_contact_at.desc().nullslast())
    )
    total = q.count()
    items = [_to_out(p) for p in q.limit(limit).offset(offset).all()]
    return ListPatientsResponse(items=items, total=total)


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(clinic_id: str, body: PatientCreate, db: Session = Depends(get_db)) -> PatientOut:
    p = Patient(
        id=str(uuid.uuid4()), clinic_id=clinic_id,
        first_name=body.first_name, last_name=body.last_name, phone=body.phone,
        dob=body.dob, email=body.email,
        crm_notes=body.crm_notes, lead_status_crm=body.lead_status_crm,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(clinic_id: str, patient_id: str, db: Session = Depends(get_db)) -> PatientOut:
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    return _to_out(p)


@router.patch("/{patient_id}", response_model=PatientOut)
def patch_patient(
    clinic_id: str, patient_id: str, body: PatientCRMUpdate, db: Session = Depends(get_db),
) -> PatientOut:
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    if body.lead_status_crm is not None:
        p.lead_status_crm = body.lead_status_crm
    if body.crm_tags is not None:
        p.crm_tags = body.crm_tags
    if body.crm_notes is not None:
        p.crm_notes = body.crm_notes
    if body.last_contact_at is not None:
        p.last_contact_at = body.last_contact_at
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{patient_id}", response_model=PatientOut)
def delete_patient(clinic_id: str, patient_id: str, db: Session = Depends(get_db)) -> PatientOut:
    """Soft delete — sets lead_status_crm='archived' to preserve FK integrity."""
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic_id).first()
    if p is None:
        raise HTTPException(404, "patient_not_found")
    p.lead_status_crm = "archived"
    db.commit()
    db.refresh(p)
    return _to_out(p)

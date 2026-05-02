"""Treatment plans router."""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Patient
from database.clinical.models import TreatmentPlan, TreatmentPlanItem, Procedure
from api.main import get_clinic

router = APIRouter(prefix="/api/v2/treatment-plans", tags=["treatment-plans"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlanItemIn(BaseModel):
    procedure_code: str
    description: Optional[str] = None
    fee: Optional[float] = None
    insurance_coverage_pct: Optional[float] = 0.0
    tooth_number: Optional[int] = None
    care_notes: Optional[str] = None


class PlanItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    plan_id: str
    sequence: int
    procedure_code: str
    description: Optional[str] = None
    fee: float
    insurance_coverage_pct: float
    tooth_number: Optional[int] = None
    care_notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class PlanIn(BaseModel):
    patient_id: str
    items: List[PlanItemIn]


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    status: str
    total_estimate: float
    insurance_estimate: float
    patient_estimate: float
    presented_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    items: List[PlanItemOut] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_plan(plan_id: str, clinic: Clinic, db: Session) -> TreatmentPlan:
    p = db.query(TreatmentPlan).filter(
        TreatmentPlan.id == plan_id,
        TreatmentPlan.clinic_id == clinic.id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Treatment plan not found")
    return p


def _compute_totals(items: List[TreatmentPlanItem]):
    total = sum(i.fee for i in items)
    insurance = sum(i.fee * (i.insurance_coverage_pct / 100.0) for i in items)
    patient = total - insurance
    return total, insurance, patient


def _resolve_items(items_in: List[PlanItemIn], clinic_id: str, plan_id: str, db: Session) -> List[TreatmentPlanItem]:
    result = []
    for seq, item in enumerate(items_in):
        fee = item.fee
        description = item.description
        if fee is None or description is None:
            proc = db.query(Procedure).filter(
                Procedure.clinic_id == clinic_id,
                Procedure.code == item.procedure_code,
            ).first()
            if proc:
                if fee is None:
                    fee = proc.default_fee
                if description is None:
                    description = proc.name
        result.append(TreatmentPlanItem(
            plan_id=plan_id,
            sequence=seq,
            procedure_code=item.procedure_code,
            description=description or item.procedure_code,
            fee=fee or 0.0,
            insurance_coverage_pct=item.insurance_coverage_pct or 0.0,
            tooth_number=item.tooth_number,
            care_notes=item.care_notes,
        ))
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=PlanOut, status_code=201)
def create_plan(body: PlanIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.id == body.patient_id,
        Patient.clinic_id == clinic.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    plan = TreatmentPlan(clinic_id=clinic.id, patient_id=body.patient_id)
    db.add(plan)
    db.flush()  # get plan.id

    items = _resolve_items(body.items, clinic.id, plan.id, db)
    for item in items:
        db.add(item)

    total, insurance, patient_est = _compute_totals(items)
    plan.total_estimate = total
    plan.insurance_estimate = insurance
    plan.patient_estimate = patient_est

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _get_plan(plan_id, clinic, db)


@router.patch("/{plan_id}/items", response_model=PlanOut)
def replace_items(plan_id: str, items_in: List[PlanItemIn], clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    plan = _get_plan(plan_id, clinic, db)
    # Delete existing items
    db.query(TreatmentPlanItem).filter(TreatmentPlanItem.plan_id == plan.id).delete()
    db.flush()

    items = _resolve_items(items_in, clinic.id, plan.id, db)
    for item in items:
        db.add(item)

    total, insurance, patient_est = _compute_totals(items)
    plan.total_estimate = total
    plan.insurance_estimate = insurance
    plan.patient_estimate = patient_est
    plan.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(plan)
    return plan


def _transition(plan_id: str, new_status: str, ts_field: Optional[str], clinic: Clinic, db: Session) -> TreatmentPlan:
    plan = _get_plan(plan_id, clinic, db)
    plan.status = new_status
    if ts_field:
        setattr(plan, ts_field, datetime.utcnow())
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/present", response_model=PlanOut)
def present_plan(plan_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _transition(plan_id, "presented", "presented_at", clinic, db)


@router.post("/{plan_id}/accept", response_model=PlanOut)
def accept_plan(plan_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _transition(plan_id, "accepted", "accepted_at", clinic, db)


@router.post("/{plan_id}/decline", response_model=PlanOut)
def decline_plan(plan_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _transition(plan_id, "declined", "declined_at", clinic, db)


@router.post("/{plan_id}/complete", response_model=PlanOut)
def complete_plan(plan_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _transition(plan_id, "completed", None, clinic, db)


@router.get("", response_model=List[PlanOut])
def list_plans(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(TreatmentPlan).filter(TreatmentPlan.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(TreatmentPlan.patient_id == patient_id)
    if status:
        q = q.filter(TreatmentPlan.status == status)
    return q.all()

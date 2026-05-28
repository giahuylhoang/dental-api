"""Insurance v2 router: claims state machine."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic
from database.ops.models import InsuranceClaim, ClaimEvent
from api.dependencies import get_authorized_clinic

router = APIRouter(prefix="/api/v2/insurance", tags=["v2-insurance"])

TERMINAL_STATUSES = {"paid"}
VALID_TRANSITIONS = {
    "draft": {"submitted"},
    "submitted": {"accepted", "rejected", "partial", "adjudicated"},
    "accepted": {"adjudicated", "paid"},
    "adjudicated": {"paid", "partial"},
    "partial": {"paid"},
    "rejected": set(),
    "paid": set(),
}


def _claim_out(c: InsuranceClaim) -> dict:
    return {
        "id": c.id,
        "clinic_id": c.clinic_id,
        "invoice_id": c.invoice_id,
        "carrier": c.carrier,
        "kind": c.kind,
        "assignment_of_benefits": c.assignment_of_benefits,
        "status": c.status,
        "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
        "adjudicated_at": c.adjudicated_at.isoformat() if c.adjudicated_at else None,
        "paid_at": c.paid_at.isoformat() if c.paid_at else None,
        "created_at": c.created_at.isoformat(),
    }


class ClaimIn(BaseModel):
    invoice_id: Optional[str] = None
    carrier: str
    kind: str  # predetermination|claim
    assignment_of_benefits: bool = False


class AdjudicateIn(BaseModel):
    response_payload: Optional[dict] = None
    paid_amount: float
    status: str  # accepted|rejected|partial


class MarkPaidIn(BaseModel):
    paid_amount: float


@router.post("/claims", status_code=201)
def create_claim(body: ClaimIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    claim = InsuranceClaim(
        clinic_id=clinic.id,
        invoice_id=body.invoice_id,
        carrier=body.carrier,
        kind=body.kind,
        assignment_of_benefits=body.assignment_of_benefits,
        status="draft",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return _claim_out(claim)


@router.get("/claims")
def list_claims(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(InsuranceClaim).filter(InsuranceClaim.clinic_id == clinic.id)
    if status:
        q = q.filter(InsuranceClaim.status == status)
    return [_claim_out(c) for c in q.all()]


@router.post("/claims/{claim_id}/submit", status_code=200)
def submit_claim(claim_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id, InsuranceClaim.clinic_id == clinic.id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")
    if "submitted" not in VALID_TRANSITIONS.get(claim.status, set()):
        raise HTTPException(400, f"Cannot submit claim in status '{claim.status}'")

    claim.status = "submitted"
    claim.submitted_at = datetime.utcnow()
    db.add(ClaimEvent(claim_id=claim.id, kind="submit_stub", payload={"note": "CDAnet transport stub"}))
    db.commit()
    db.refresh(claim)
    return _claim_out(claim)


@router.post("/claims/{claim_id}/adjudicate", status_code=200)
def adjudicate_claim(claim_id: str, body: AdjudicateIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id, InsuranceClaim.clinic_id == clinic.id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")

    new_status = body.status
    if new_status not in VALID_TRANSITIONS.get(claim.status, set()):
        raise HTTPException(400, f"Cannot transition from '{claim.status}' to '{new_status}'")

    claim.status = new_status
    claim.adjudicated_at = datetime.utcnow()
    claim.response_payload = body.response_payload
    if new_status == "rejected":
        # paid_amount = 0 for rejected
        pass
    db.add(ClaimEvent(claim_id=claim.id, kind="adjudicated", payload={"paid_amount": body.paid_amount, "status": new_status}))
    db.commit()
    db.refresh(claim)
    return _claim_out(claim)


@router.post("/claims/{claim_id}/mark-paid", status_code=200)
def mark_paid(claim_id: str, body: MarkPaidIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id, InsuranceClaim.clinic_id == clinic.id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")
    if "paid" not in VALID_TRANSITIONS.get(claim.status, set()):
        raise HTTPException(400, f"Cannot mark paid from status '{claim.status}'")

    claim.status = "paid"
    claim.paid_at = datetime.utcnow()
    db.add(ClaimEvent(claim_id=claim.id, kind="paid", payload={"paid_amount": body.paid_amount}))
    db.commit()
    db.refresh(claim)
    return _claim_out(claim)

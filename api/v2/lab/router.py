"""Lab router: vendors and lab cases."""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic
from database.clinical.models import LabVendor, LabCase, LabCaseEvent, DentureCase
from api.dependencies import get_authorized_clinic
from clients.lab_case_numbering import next_lab_case_number

router = APIRouter(prefix="/api/v2/lab", tags=["lab"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VendorIn(BaseModel):
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sla_days: Optional[int] = None
    price_list: Optional[dict] = {}
    is_active: Optional[bool] = True


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sla_days: Optional[int] = None
    price_list: Optional[dict] = {}
    is_active: Optional[bool] = True


class LabCaseIn(BaseModel):
    denture_case_id: str
    vendor_id: str
    sent_at: Optional[datetime] = None
    due_back_at: Optional[datetime] = None
    lab_fee: Optional[float] = None
    courier_tracking: Optional[str] = None
    treatment_plan_id: Optional[str] = None


class LabCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    denture_case_id: str
    vendor_id: str
    case_number: Optional[str] = None
    treatment_plan_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    due_back_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    status: str
    remake_of_id: Optional[str] = None
    remake_reason: Optional[str] = None
    lab_fee: Optional[float] = None
    courier_tracking: Optional[str] = None
    created_at: Optional[datetime] = None


class RemakeIn(BaseModel):
    reason: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_vendor(vendor_id: str, clinic: Clinic, db: Session) -> LabVendor:
    v = db.query(LabVendor).filter(LabVendor.id == vendor_id, LabVendor.clinic_id == clinic.id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return v


def _get_lab_case(case_id: str, clinic: Clinic, db: Session) -> LabCase:
    c = db.query(LabCase).filter(LabCase.id == case_id, LabCase.clinic_id == clinic.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Lab case not found")
    return c


def _add_event(db: Session, lab_case_id: str, kind: str, payload: dict = None):
    db.add(LabCaseEvent(lab_case_id=lab_case_id, kind=kind, payload=payload or {}))


# ---------------------------------------------------------------------------
# Vendor endpoints
# ---------------------------------------------------------------------------

@router.get("/vendors", response_model=List[VendorOut])
def list_vendors(clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    return db.query(LabVendor).filter(LabVendor.clinic_id == clinic.id).all()


@router.post("/vendors", response_model=VendorOut, status_code=201)
def create_vendor(body: VendorIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    obj = LabVendor(clinic_id=clinic.id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/vendors/{vendor_id}", response_model=VendorOut)
def update_vendor(vendor_id: str, body: VendorIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    v = _get_vendor(vendor_id, clinic, db)
    for k, val in body.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/vendors/{vendor_id}", status_code=204)
def delete_vendor(vendor_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    v = _get_vendor(vendor_id, clinic, db)
    db.delete(v)
    db.commit()


# ---------------------------------------------------------------------------
# Lab case endpoints
# ---------------------------------------------------------------------------

@router.post("/cases", response_model=LabCaseOut, status_code=201)
def create_lab_case(body: LabCaseIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    # Verify denture case belongs to clinic
    dc = db.query(DentureCase).filter(
        DentureCase.id == body.denture_case_id,
        DentureCase.clinic_id == clinic.id,
    ).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Denture case not found")
    _get_vendor(body.vendor_id, clinic, db)
    case_num = next_lab_case_number(db, clinic.id)
    obj = LabCase(clinic_id=clinic.id, status="draft", case_number=case_num, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


class StatusPatchIn(BaseModel):
    status: str
    remake_reason: Optional[str] = None


@router.patch("/cases/{case_id}/status", response_model=LabCaseOut)
def patch_lab_case_status(
    case_id: str,
    body: StatusPatchIn,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    """Generic status setter — used by the kanban drag-and-drop."""
    c = _get_lab_case(case_id, clinic, db)
    new_status = body.status
    allowed = {"draft", "sent", "in_progress", "returned", "remake", "cancelled"}
    if new_status not in allowed:
        raise HTTPException(400, f"Invalid status '{new_status}'")
    now = datetime.utcnow()
    c.status = new_status
    c.updated_at = now
    if new_status == "sent" and not c.sent_at:
        c.sent_at = now
    if new_status == "returned" and not c.returned_at:
        c.returned_at = now
    payload = {"reason": body.remake_reason} if body.remake_reason else None
    _add_event(db, c.id, f"status_set_{new_status}", payload)
    db.commit()
    db.refresh(c)
    return c


@router.post("/cases/{case_id}/send", response_model=LabCaseOut)
def send_lab_case(case_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    c = _get_lab_case(case_id, clinic, db)
    c.status = "sent"
    c.sent_at = c.sent_at or datetime.utcnow()
    c.updated_at = datetime.utcnow()
    _add_event(db, c.id, "sent")
    db.commit()
    db.refresh(c)
    return c


@router.post("/cases/{case_id}/return", response_model=LabCaseOut)
def return_lab_case(case_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    c = _get_lab_case(case_id, clinic, db)
    c.status = "returned"
    c.returned_at = datetime.utcnow()
    c.updated_at = datetime.utcnow()
    _add_event(db, c.id, "returned")
    db.commit()
    db.refresh(c)
    return c


@router.post("/cases/{case_id}/remake", response_model=LabCaseOut, status_code=201)
def remake_lab_case(case_id: str, body: RemakeIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    original = _get_lab_case(case_id, clinic, db)
    original.status = "remake"
    original.updated_at = datetime.utcnow()
    _add_event(db, original.id, "remake_requested", {"reason": body.reason})
    new_case = LabCase(
        clinic_id=original.clinic_id,
        denture_case_id=original.denture_case_id,
        vendor_id=original.vendor_id,
        lab_fee=original.lab_fee,
        status="draft",
        remake_of_id=original.id,
        remake_reason=body.reason,
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


@router.get("/cases", response_model=List[LabCaseOut])
def list_lab_cases(
    status: Optional[str] = None,
    vendor_id: Optional[str] = None,
    denture_case_id: Optional[str] = None,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(LabCase).filter(LabCase.clinic_id == clinic.id)
    if status:
        q = q.filter(LabCase.status == status)
    if vendor_id:
        q = q.filter(LabCase.vendor_id == vendor_id)
    if denture_case_id:
        q = q.filter(LabCase.denture_case_id == denture_case_id)
    return q.all()

"""Billing v2 router: invoices, payments."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic
from database.ops.models import Invoice, InvoiceLine, Payment
from api.main import get_clinic

router = APIRouter(prefix="/api/v2/billing", tags=["v2-billing"])


class LineIn(BaseModel):
    procedure_code: Optional[str] = None
    description: Optional[str] = None
    qty: int = 1
    unit_price: float


class InvoiceIn(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    treatment_plan_id: Optional[str] = None
    lines: List[LineIn]
    gst_rate: float = 0.05


class InvoiceOut(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    appointment_id: Optional[str] = None
    status: str
    subtotal: float
    gst: float
    total: float
    balance: float
    currency: str
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentIn(BaseModel):
    method: str
    amount: float
    reference: Optional[str] = None
    notes: Optional[str] = None


def _invoice_out(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "clinic_id": inv.clinic_id,
        "patient_id": inv.patient_id,
        "appointment_id": inv.appointment_id,
        "status": inv.status,
        "subtotal": float(inv.subtotal),
        "gst": float(inv.gst),
        "total": float(inv.total),
        "balance": float(inv.balance),
        "currency": inv.currency,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "due_at": inv.due_at.isoformat() if inv.due_at else None,
        "created_at": inv.created_at.isoformat(),
    }


@router.post("/invoices", status_code=201)
def create_invoice(body: InvoiceIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    subtotal = Decimal("0")
    line_objs = []
    for i, line in enumerate(body.lines):
        line_total = Decimal(str(line.unit_price)) * line.qty
        subtotal += line_total
        line_objs.append(InvoiceLine(
            sequence=i + 1,
            procedure_code=line.procedure_code,
            description=line.description,
            qty=line.qty,
            unit_price=Decimal(str(line.unit_price)),
            total=line_total,
        ))

    gst = (subtotal * Decimal(str(body.gst_rate))).quantize(Decimal("0.01"))
    total = subtotal + gst

    inv = Invoice(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        appointment_id=body.appointment_id,
        treatment_plan_id=body.treatment_plan_id,
        status="draft",
        subtotal=subtotal,
        gst=gst,
        total=total,
        balance=total,
        currency="CAD",
    )
    db.add(inv)
    db.flush()
    for lo in line_objs:
        lo.invoice_id = inv.id
        db.add(lo)
    db.commit()
    db.refresh(inv)
    return _invoice_out(inv)


@router.get("/invoices")
def list_invoices(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice).filter(Invoice.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(Invoice.patient_id == patient_id)
    if status:
        q = q.filter(Invoice.status == status)
    return [_invoice_out(inv) for inv in q.all()]


@router.post("/invoices/{inv_id}/issue", status_code=200)
def issue_invoice(inv_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id, Invoice.clinic_id == clinic.id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status != "draft":
        raise HTTPException(400, f"Cannot issue invoice in status '{inv.status}'")
    now = datetime.utcnow()
    inv.status = "issued"
    inv.issued_at = now
    inv.due_at = now + timedelta(days=30)
    db.commit()
    db.refresh(inv)
    return _invoice_out(inv)


@router.post("/invoices/{inv_id}/payments", status_code=201)
def record_payment(inv_id: str, body: PaymentIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id, Invoice.clinic_id == clinic.id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status == "void":
        raise HTTPException(400, "Cannot record payment on voided invoice")

    payment = Payment(
        invoice_id=inv.id,
        method=body.method,
        amount=Decimal(str(body.amount)),
        reference=body.reference,
        notes=body.notes,
    )
    db.add(payment)

    new_balance = Decimal(str(inv.balance)) - Decimal(str(body.amount))
    inv.balance = new_balance
    if new_balance <= 0:
        inv.status = "paid"
    else:
        inv.status = "partial"

    db.commit()
    db.refresh(inv)
    return _invoice_out(inv)


@router.post("/invoices/{inv_id}/void", status_code=200)
def void_invoice(inv_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id, Invoice.clinic_id == clinic.id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status == "paid":
        raise HTTPException(400, "Cannot void a paid invoice")
    inv.status = "void"
    db.commit()
    db.refresh(inv)
    return _invoice_out(inv)

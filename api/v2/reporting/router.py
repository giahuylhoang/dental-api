"""Reporting router: real KPIs aggregated from invoices, appointments, lab cases."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_authorized_clinic
from database.connection import get_db
from database.clinical.models import LabCase, LabVendor
from database.models import Appointment, AppointmentStatus, Clinic, Provider
from database.ops.models import Invoice, InvoiceLine

router = APIRouter(prefix="/api/v2/reporting", tags=["v2-reporting"])


@router.get("/kpi")
def get_kpi(clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    """Top-line KPIs for the dashboard."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    production_this_month = (
        db.query(func.coalesce(func.sum(Invoice.total), 0))
        .filter(
            Invoice.clinic_id == clinic.id,
            Invoice.status.in_(["issued", "partial", "paid"]),
            Invoice.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    # AR aging buckets — based on outstanding `balance` and days since `due_at` (or `created_at`)
    ar_buckets = {"0–30": 0.0, "31–60": 0.0, "61–90": 0.0, "90+": 0.0}
    open_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.clinic_id == clinic.id,
            Invoice.status.in_(["issued", "partial"]),
            Invoice.balance > 0,
        )
        .all()
    )
    for inv in open_invoices:
        ref = inv.due_at or inv.issued_at or inv.created_at or now
        days = max(0, (now - ref).days)
        bucket = (
            "0–30" if days <= 30
            else "31–60" if days <= 60
            else "61–90" if days <= 90
            else "90+"
        )
        ar_buckets[bucket] += float(inv.balance or 0)

    # No-show rate over last 90 days
    cutoff = now - timedelta(days=90)
    total_appts = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.clinic_id == clinic.id, Appointment.start_time >= cutoff)
        .scalar()
        or 0
    )
    no_shows = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.clinic_id == clinic.id,
            Appointment.start_time >= cutoff,
            Appointment.status == AppointmentStatus.NO_SHOW,
        )
        .scalar()
        or 0
    )
    no_show_rate = (no_shows / total_appts) if total_appts else 0.0

    # Lab cost per case — average of `lab_fee` across all lab cases this clinic
    avg_lab_fee = (
        db.query(func.coalesce(func.avg(LabCase.lab_fee), 0))
        .filter(LabCase.clinic_id == clinic.id, LabCase.lab_fee.isnot(None))
        .scalar()
        or 0
    )

    return {
        "production_this_month": float(production_this_month),
        "ar_aging": [{"bucket": k, "amount": round(v, 2)} for k, v in ar_buckets.items()],
        "no_show_rate": round(float(no_show_rate), 4),
        "lab_cost_per_case": round(float(avg_lab_fee), 2),
    }


@router.get("/production-by-provider")
def production_by_provider(
    clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)
):
    """Total production per provider this month, joined via appointment.provider_id."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        db.query(
            Provider.id,
            Provider.name,
            Provider.title,
            func.coalesce(func.sum(Invoice.total), 0).label("production"),
        )
        .outerjoin(
            Appointment,
            (Appointment.provider_id == Provider.id)
            & (Appointment.clinic_id == clinic.id),
        )
        .outerjoin(
            Invoice,
            (Invoice.appointment_id == Appointment.id)
            & (Invoice.created_at >= month_start)
            & (Invoice.status.in_(["issued", "partial", "paid"])),
        )
        .filter(Provider.clinic_id == clinic.id)
        .group_by(Provider.id, Provider.name, Provider.title)
        .all()
    )

    return [
        {
            "provider_name": (
                f"{r.title} {r.name}" if r.title else r.name
            ),
            "production": float(r.production or 0),
        }
        for r in rows
        if (r.production or 0) > 0
    ] or [
        # Fallback: surface providers with zero production so the UI isn't empty
        {
            "provider_name": (f"{r.title} {r.name}" if r.title else r.name),
            "production": 0.0,
        }
        for r in rows[:6]
    ]


@router.get("/remake-rate-by-lab")
def remake_rate_by_lab(
    clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)
):
    """Per lab vendor: total cases + ratio of remakes."""
    rows = (
        db.query(
            LabVendor.id,
            LabVendor.name,
            func.count(LabCase.id).label("total_cases"),
        )
        .outerjoin(LabCase, LabCase.vendor_id == LabVendor.id)
        .filter(LabVendor.clinic_id == clinic.id)
        .group_by(LabVendor.id, LabVendor.name)
        .all()
    )

    out = []
    for r in rows:
        total = int(r.total_cases or 0)
        remakes = (
            db.query(func.count(LabCase.id))
            .filter(LabCase.vendor_id == r.id, LabCase.remake_of_id.isnot(None))
            .scalar()
            or 0
        )
        rate = (remakes / total) if total else 0.0
        out.append(
            {
                "lab_name": r.name,
                "remake_rate": round(float(rate), 4),
                "total_cases": total,
            }
        )
    return out

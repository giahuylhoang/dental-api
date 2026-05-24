"""GET /api/portal/clinics/{cid}/dashboard — KPI rollup via SQL aggregations."""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import CallLog, Patient

router = APIRouter()


@router.get("")
def dashboard(clinic_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    calls_total = (
        db.query(func.count(CallLog.id))
        .filter(CallLog.clinic_id == clinic_id)
        .scalar()
        or 0
    )
    calls_booked = (
        db.query(func.count(CallLog.id))
        .filter(CallLog.clinic_id == clinic_id, CallLog.outcome == "booked")
        .scalar()
        or 0
    )
    patients_total = (
        db.query(func.count(Patient.id))
        .filter(Patient.clinic_id == clinic_id)
        .scalar()
        or 0
    )

    return {
        "calls_total": calls_total,
        "calls_booked": calls_booked,
        "patients_total": patients_total,
    }

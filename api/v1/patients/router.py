"""v1 patients router — /api/patients CRUD + /api/patients/verify."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_authorized_clinic, get_db
from database.models import Clinic, Patient

from api.v1.patients.schemas import (
    PatientCreateRequest,
    PatientResponse,
    PatientVerifyRequest,
    PatientVerifyResponse,
)

logger = logging.getLogger("dental-receptionist")

router = APIRouter(prefix="/api/patients", tags=["patients"])


def _phone_digits(phone: Optional[str]) -> str:
    """Reduce a phone string to its digits. Used to match patients regardless
    of how the caller formatted the number (E.164, dashed, parenthesized).
    Stored Patient.phone can be any of those forms — historical data is mixed."""
    if not phone:
        return ""
    return "".join(c for c in phone if c.isdigit())


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """List patients with optional filters."""
    query = db.query(Patient).filter(Patient.clinic_id == clinic.id)
    if phone:
        query = query.filter(Patient.phone == phone)
    if email:
        query = query.filter(Patient.email == email)
    patients = query.all()
    return [PatientResponse.model_validate(p) for p in patients]


@router.post("/verify", response_model=PatientVerifyResponse)
async def verify_patient(
    request: PatientVerifyRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """
    Verify patient identity by phone number and date of birth.

    This is a secure endpoint that only returns patient_id if verification succeeds.
    No other patient data is exposed. Returns 404 if verification fails.

    Args:
        request: PatientVerifyRequest with phone and dob

    Returns:
        PatientVerifyResponse with patient_id if verification succeeds
        Raises 404 if no patient matches or verification fails
    """
    try:
        # Normalize phone to digits only for comparison.
        phone_digits = _phone_digits(request.phone)

        # Parse DOB
        from datetime import date as date_type
        dob_date = datetime.strptime(request.dob, '%Y-%m-%d').date()

        # Narrow by suffix (last 10 digits) using an indexable LIKE, then
        # suffix-compare in Python — stored phones can be E.164
        # ("+13682990959"), digits-only ("13682990959"), or formatted
        # ("(403) 555-0199"), and lookup phones may or may not include the
        # country code. Comparing the last 10 digits collapses all of those
        # to the same NANP subscriber number.
        suffix = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits
        candidates = db.query(Patient).filter(
            Patient.clinic_id == clinic.id,
            Patient.phone.like(f"%{suffix}"),
        ).all() if suffix else []
        patient = next(
            (p for p in candidates if _phone_digits(p.phone).endswith(suffix)),
            None,
        )

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Verify DOB matches
        if not patient.dob:
            raise HTTPException(status_code=404, detail="Patient verification failed")

        # Compare DOB (handle both date and string formats)
        patient_dob = patient.dob
        if isinstance(patient_dob, str):
            patient_dob = datetime.strptime(patient_dob, '%Y-%m-%d').date()

        if patient_dob != dob_date:
            raise HTTPException(status_code=404, detail="Patient verification failed")

        # Verification successful - return only patient_id
        return PatientVerifyResponse(patient_id=patient.id, verified=True)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}. Use YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying patient: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during verification")


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Get patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.post("", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Create new patient."""
    try:
        # Convert Pydantic model to dict
        patient_dict = patient_data.model_dump(exclude_none=True)

        # Convert dob string to date if provided
        if 'dob' in patient_dict and patient_dict['dob']:
            from datetime import date as date_type
            if isinstance(patient_dict['dob'], str):
                patient_dict['dob'] = datetime.strptime(patient_dict['dob'], '%Y-%m-%d').date()

        patient = Patient(clinic_id=clinic.id, **patient_dict)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return PatientResponse.model_validate(patient)
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = str(e)
        print(f"Error creating patient: {error_detail}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {error_detail}")


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: dict,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Update patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in patient_data.items():
        if hasattr(patient, key):
            setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return PatientResponse.model_validate(patient)


class CRMRollupBody(BaseModel):
    """PUT /api/patients/{id}/crm-rollup — CRM-only allowlist."""
    lead_status_crm: Optional[str] = None
    crm_tags: Optional[Dict[str, Any]] = None
    crm_notes: Optional[str] = None
    last_contact_at: Optional[datetime] = None

    model_config = {"extra": "forbid"}


@router.put("/{patient_id}/crm-rollup")
def crm_rollup(
    patient_id: str,
    body: CRMRollupBody,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Update CRM-only columns on a Patient (identity fields are not accepted)."""
    p = db.query(Patient).filter_by(id=patient_id, clinic_id=clinic.id).first()
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
    return {"id": patient_id, "status": "ok"}

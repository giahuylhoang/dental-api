"""v1 clinics router — /api/clinics, /api/clinics/me."""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic

from api.v1.clinics.schemas import (
    ClinicBySpecRequest,
    ClinicCreateRequest,
    ClinicResponse,
    ClinicUpdateRequest,
)

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


def _require_admin_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """Inline dep validating the X-Admin-Token header against DENTAL_ADMIN_TOKEN env.

    Defined here (not in a shared auth module) to keep S1's scope tight and to
    avoid forcing other endpoints to opt into a new auth dep. Returns None on
    success, raises 401 on mismatch OR when the header is missing entirely.
    """
    expected = os.environ.get("DENTAL_ADMIN_TOKEN")
    if not expected or not x_admin_token or x_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid X-Admin-Token",
        )


@router.post("", response_model=ClinicResponse)
async def create_clinic(
    request: ClinicCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new clinic (admin/setup)."""
    existing = db.query(Clinic).filter(Clinic.id == request.id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Clinic already exists: {request.id}")
    clinic = Clinic(
        id=request.id,
        name=request.name,
        timezone=request.timezone or "America/Edmonton",
        working_hour_start=request.working_hour_start or 9,
        working_hour_end=request.working_hour_end or 17,
        address=request.address,
        contact_phone=request.contact_phone,
        booking_notification_email=request.booking_notification_email,
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.get("/me", response_model=ClinicResponse)
async def get_clinic_me(clinic: Clinic = Depends(get_clinic)):
    """Get current clinic config (from X-Clinic-Id header)."""
    return ClinicResponse.model_validate(clinic)


@router.patch("/me", response_model=ClinicResponse)
async def patch_clinic_me(
    request: ClinicUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update current clinic fields (from X-Clinic-Id)."""
    updates = request.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if hasattr(clinic, key):
            setattr(clinic, key, value)
    clinic.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.post(
    "/by-spec",
    response_model=ClinicResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
)
def create_or_update_clinic_by_spec(
    payload: ClinicBySpecRequest,
    db: Session = Depends(get_db),
) -> Clinic:
    """Provision or update a clinic from an enroll_clinic.py spec.

    Idempotent: looks up by id; updates non-null fields on hit, inserts on miss.
    Returns the row (post-write) as ClinicResponse.
    """
    existing = db.query(Clinic).filter(Clinic.id == payload.id).one_or_none()
    if existing is None:
        clinic = Clinic(id=payload.id, name=payload.name)
        for field in ("timezone", "working_hour_start", "working_hour_end",
                      "address", "contact_phone", "booking_notification_email"):
            v = getattr(payload, field)
            if v is not None:
                setattr(clinic, field, v)
        db.add(clinic)
    else:
        clinic = existing
        clinic.name = payload.name
        for field in ("timezone", "working_hour_start", "working_hour_end",
                      "address", "contact_phone", "booking_notification_email"):
            v = getattr(payload, field)
            if v is not None:
                setattr(clinic, field, v)
    db.commit()
    db.refresh(clinic)
    return clinic

"""v1 clinics router — /api/clinics, /api/clinics/me."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import (
    get_authorized_clinic,
    get_current_uid,
    get_db,
    get_internal_caller,
)
from database.auth import UserClinicMembership
from database.models import Clinic

from api.v1.clinics.resolver import (
    resolve_clinic_config,
    resolve_clinic_id_for_did,
    resolve_clinic_routing,
)
from api.v1.clinics.schemas import (
    ClinicByDidResponse,
    ClinicConfigResponse,
    ClinicCreateRequest,
    ClinicResponse,
    ClinicRoutingResponse,
    ClinicSummary,
    ClinicsListResponse,
    ClinicUpdateRequest,
)

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


@router.get("", response_model=ClinicsListResponse)
async def list_clinics(
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Return the caller's authorized clinics.

    Drives the CRM/admin sidebar switcher. In bypass mode (dev/tests with
    ADMIN_AUTH_BYPASS=true) returns every clinic in the DB — uid is the
    dev-skip placeholder and has no memberships.
    """
    from api.dependencies.auth import ADMIN_AUTH_BYPASS
    if ADMIN_AUTH_BYPASS:
        rows = db.query(Clinic).order_by(Clinic.name).all()
    else:
        rows = (
            db.query(Clinic)
            .join(UserClinicMembership, UserClinicMembership.clinic_id == Clinic.id)
            .filter(UserClinicMembership.uid == uid)
            .order_by(Clinic.name)
            .all()
        )
    return {"clinics": [ClinicSummary.model_validate(r) for r in rows]}


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
async def get_clinic_me(clinic: Clinic = Depends(get_authorized_clinic)):
    """Get current clinic config (from X-Clinic-Id, authorized via uid+membership)."""
    return ClinicResponse.model_validate(clinic)


@router.patch("/me", response_model=ClinicResponse)
async def patch_clinic_me(
    request: ClinicUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Update current clinic fields (from X-Clinic-Id, authorized via uid+membership)."""
    updates = request.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if hasattr(clinic, key):
            setattr(clinic, key, value)
    clinic.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.get(
    "/by-did/{did:path}",
    response_model=ClinicByDidResponse,
    dependencies=[Depends(get_internal_caller)],
)
async def get_clinic_by_did(did: str, db: Session = Depends(get_db)):
    """Reverse-index a dialed DID to its owning clinic_id (404 if none)."""
    clinic_id = resolve_clinic_id_for_did(db, did)
    if clinic_id is None:
        raise HTTPException(status_code=404, detail=f"No clinic owns DID: {did}")
    return {"clinic_id": clinic_id}


@router.get(
    "/{clinic_id}/config",
    response_model=ClinicConfigResponse,
    dependencies=[Depends(get_internal_caller)],
)
async def get_clinic_config(clinic_id: str, db: Session = Depends(get_db)):
    """Return the fully merged clinic config (practice_type defaults + overrides + routing)."""
    cfg = resolve_clinic_config(db, clinic_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
    return cfg


@router.get(
    "/{clinic_id}/routing",
    response_model=ClinicRoutingResponse,
    dependencies=[Depends(get_internal_caller)],
)
async def get_clinic_routing_endpoint(clinic_id: str, db: Session = Depends(get_db)):
    """Routing-only payload for the routing_webhook. ~10x smaller than /config."""
    routing = resolve_clinic_routing(db, clinic_id)
    if routing is None:
        raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
    return routing

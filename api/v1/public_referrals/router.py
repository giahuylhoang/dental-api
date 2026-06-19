"""Public referral endpoints (internal-secret gated; called via the booking BFF).

Two JSON steps (files go browser→GCS directly via signed URLs):
  POST /api/public/referrals            → create referral + per-file signed PUT URLs
  POST /api/public/referrals/{id}/complete → verify uploads, record docs, email clinic
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.dependencies.auth import require_internal_secret
from database.connection import get_db
from database.models import Clinic
from services.referrals import create_referral, complete_referral
from services.storage import get_storage_backend
from .schemas import (
    ReferralCompleteRequest,
    ReferralCompleteResponse,
    ReferralCreateRequest,
    ReferralCreateResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public-referrals"])


def _resolve_clinic(db: Session, clinic_id: str) -> Clinic:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if clinic is None:
        raise HTTPException(status_code=404, detail="clinic_not_found")
    return clinic


@router.post("/referrals", response_model=ReferralCreateResponse)
def create_public_referral(
    payload: ReferralCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_secret),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    clinic = _resolve_clinic(db, x_clinic_id)
    submit_ip = request.client.host if request.client else None
    referral, tickets = create_referral(
        db, clinic=clinic, payload=payload, submit_ip=submit_ip,
        storage=get_storage_backend(),
    )
    db.commit()
    db.refresh(referral)
    return ReferralCreateResponse(
        referral_id=referral.id,
        status=referral.status.value,
        uploads=tickets,
    )


@router.post("/referrals/{referral_id}/complete", response_model=ReferralCompleteResponse)
def complete_public_referral(
    referral_id: str,
    background_tasks: BackgroundTasks,
    payload: ReferralCompleteRequest | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_secret),
    x_clinic_id: str = Header("default", alias="X-Clinic-Id"),
):
    clinic = _resolve_clinic(db, x_clinic_id)
    referral = complete_referral(
        db, background_tasks, clinic=clinic, referral_id=referral_id,
        payload=payload or ReferralCompleteRequest(),
        storage=get_storage_backend(),
    )
    return ReferralCompleteResponse(
        referral_id=referral.id,
        status=referral.status.value,
        documents=len(referral.documents),
    )

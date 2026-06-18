"""Firebase-token-based auth for dental-api.

Two layers:
- get_current_uid: verifies an `Authorization: Bearer <id-token>` header
  against Firebase and returns the user's uid.
- get_authorized_clinic: resolves the X-Clinic-Id header and confirms it
  is one of the uid's authorized clinics in user_clinic_memberships.

Plus get_internal_caller for routing-webhook endpoints — those have no
user, so they ride on a shared `X-Internal-Secret` header.

`ADMIN_AUTH_BYPASS=true` env var short-circuits all three. Used:
- in tests (conftest sets it on)
- during the cutover window before flipping enforcement on
"""
import logging
import os
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from database.auth import UserClinicMembership
from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID


logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


ADMIN_AUTH_BYPASS: bool = _env_bool("ADMIN_AUTH_BYPASS", default=False)
INTERNAL_SECRET: Optional[str] = os.getenv("DENTAL_API_INTERNAL_SECRET")


def init_firebase_admin() -> None:
    """Initialize the Firebase Admin SDK exactly once at process start.

    Skipped in bypass mode so local dev does not require service-account
    credentials. On Cloud Run, runtime ADC is used automatically.
    """
    if ADMIN_AUTH_BYPASS:
        logger.warning("ADMIN_AUTH_BYPASS=true — Firebase Admin SDK init skipped.")
        return
    if firebase_admin._apps:
        return
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    else:
        # On Cloud Run, ADC is picked up from the runtime service account.
        firebase_admin.initialize_app()
    logger.info("Firebase Admin SDK initialized.")


def get_current_uid(
    authorization: Optional[str] = Header(None),
) -> str:
    """Verify the Bearer token and return its uid. 401 on any failure."""
    if ADMIN_AUTH_BYPASS:
        return "dev-skip-uid"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")
    return decoded["uid"]


def get_authorized_clinic(
    uid: str = Depends(get_current_uid),
    x_clinic_id: Optional[str] = Header(None, alias="X-Clinic-Id"),
    db: Session = Depends(get_db),
) -> Clinic:
    """Resolve and authorize the Clinic referenced by X-Clinic-Id.

    Enforcement order:
    1. (Bypass mode) Just look up the Clinic, no membership check.
    2. Look up the uid's membership rows.
    3. Reject 403 if X-Clinic-Id is not in the allowed set.
    4. Look up the Clinic; 404 if missing.
    """
    # Legacy compatibility: in bypass mode, fall back to the default clinic
    # when the caller omits X-Clinic-Id. Non-bypass mode requires the
    # header explicitly — fail-closed.
    if ADMIN_AUTH_BYPASS and not x_clinic_id:
        x_clinic_id = DEFAULT_CLINIC_ID
    if not x_clinic_id:
        raise HTTPException(status_code=401, detail="missing_clinic_header")

    if ADMIN_AUTH_BYPASS:
        clinic = db.query(Clinic).filter(Clinic.id == x_clinic_id).first()
        if not clinic:
            raise HTTPException(status_code=404, detail="clinic_not_found")
        return clinic
    allowed = {
        m.clinic_id
        for m in db.query(UserClinicMembership).filter(UserClinicMembership.uid == uid).all()
    }
    if x_clinic_id not in allowed:
        raise HTTPException(status_code=403, detail="clinic_forbidden")
    clinic = db.query(Clinic).filter(Clinic.id == x_clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="clinic_not_found")
    return clinic


def get_internal_caller(
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret"),
) -> None:
    """Gate for non-user infra callers (routing webhook, voice agent).

    No user identity here; just a shared secret. Rotate via
    DENTAL_API_INTERNAL_SECRET env var.
    """
    if ADMIN_AUTH_BYPASS:
        return
    if not INTERNAL_SECRET or x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="internal_auth_failed")


def require_internal_secret(
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret"),
) -> None:
    """Enforce the shared internal secret for internet-facing endpoints, REGARDLESS
    of ADMIN_AUTH_BYPASS. Unlike get_internal_caller, bypass does NOT skip this — so
    endpoints exposed to the public internet (via the booking BFF) stay protected even
    when the rest of the API is in bypass mode. If no secret is configured
    (INTERNAL_SECRET is unset — local/dev/test), the check is skipped so dev/tests work.
    """
    if INTERNAL_SECRET and x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="internal_auth_failed")

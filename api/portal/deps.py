"""Firebase ID token verification + clinic-claim enforcement for /api/portal/*."""

from __future__ import annotations

import logging
import os
from typing import List

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.auth.memberships import UserClinicMembership

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False


_log = logging.getLogger("api.portal.deps")

_app_initialized = False


def _ensure_app() -> None:
    """Init the default firebase_admin app once."""
    global _app_initialized
    if _app_initialized:
        return
    if not _FIREBASE_AVAILABLE:
        raise RuntimeError("firebase-admin not installed")
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    _app_initialized = True


class PortalUser(BaseModel):
    uid: str
    email: str
    clinic_ids: List[str]
    role: str = "readonly"


def get_portal_user(authorization: str = Header(default="")) -> PortalUser:
    """Verify Firebase ID token from Authorization header, extract claims."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "empty token")

    _ensure_app()
    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}")

    clinic_ids = decoded.get("clinic_ids")
    if not clinic_ids and "clinic_id" in decoded:
        clinic_ids = [decoded["clinic_id"]]
    if not clinic_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no clinic claim on token")

    return PortalUser(
        uid=decoded["uid"],
        email=decoded.get("email", ""),
        clinic_ids=list(clinic_ids),
        role=decoded.get("role", "readonly"),
    )


def require_clinic_access(
    clinic_id: str,
    user: "PortalUser" = Depends(get_portal_user),
    db: Session = Depends(get_db),
) -> str:
    """Authorize the bearer of this token for {clinic_id}.

    Soft-fallback design: DB membership is canonical; token claim is a
    temporary safety net during the cutover window. See
    docs/superpowers/specs/2026-05-28-admin-portal-auth-design.md.
    """
    try:
        row = (
            db.query(UserClinicMembership)
            .filter_by(uid=user.uid, clinic_id=clinic_id)
            .first()
        )
    except (OperationalError, ProgrammingError) as exc:
        # The user_clinic_memberships table is missing — CRM auth plan
        # migration was not deployed. Fail loud rather than silently
        # falling back to claims, which would mask a deploy bug.
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "membership table not initialized; deploy CRM auth migration first",
        ) from exc

    if row is not None:
        return clinic_id

    # Fallback to the token claim during cutover. Emit a structured warn
    # so ops can tell when memberships are fully backfilled and the
    # fallback can be removed.
    if clinic_id in (user.clinic_ids or []):
        _log.warning(
            "portal_membership_missing uid=%s clinic_id=%s email=%s",
            user.uid, clinic_id, user.email,
        )
        return clinic_id

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        f"no_access_to_clinic:{clinic_id}",
    )

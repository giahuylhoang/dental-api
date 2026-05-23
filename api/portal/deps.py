"""Firebase ID token verification + clinic-claim enforcement for /api/portal/*."""

from __future__ import annotations

import os
from typing import List

from fastapi import Header, HTTPException, status
from pydantic import BaseModel

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False


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


def require_clinic_access(clinic_id: str, user: PortalUser) -> str:
    """Raise 403 if the verified user's claims do not grant this clinic_id."""
    if clinic_id not in user.clinic_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"no_access_to_clinic:{clinic_id}")
    return clinic_id

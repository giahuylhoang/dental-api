"""Shared FastAPI dependencies.

Re-exports the legacy `get_clinic` etc. for callers that haven't migrated
to the auth-aware versions, plus the new auth helpers.
"""
from api.dependencies._legacy import get_db, get_clinic_id, get_clinic  # noqa: F401
from api.dependencies.auth import (  # noqa: F401
    ADMIN_AUTH_BYPASS,
    get_current_uid,
    get_authorized_clinic,
    get_internal_caller,
    require_internal_secret,
    init_firebase_admin,
)

__all__ = [
    "get_db",
    "get_clinic_id",
    "get_clinic",
    "ADMIN_AUTH_BYPASS",
    "get_current_uid",
    "get_authorized_clinic",
    "get_internal_caller",
    "require_internal_secret",
    "init_firebase_admin",
]

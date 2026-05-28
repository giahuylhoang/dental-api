"""Shared FastAPI dependencies for the v1 API surface.

Re-exported from api.main for backwards-compatibility with v2 routers and
tests that do `from api.main import get_clinic`.
"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID


# Multi-tenant: resolve clinic from X-Clinic-Id header (default: "default")
def get_clinic_id(request: Request) -> str:
    clinic_id = request.headers.get("X-Clinic-Id", DEFAULT_CLINIC_ID)
    return clinic_id.strip() or DEFAULT_CLINIC_ID


def get_clinic(db: Session = Depends(get_db), clinic_id: str = Depends(get_clinic_id)):
    """Resolve Clinic by X-Clinic-Id. Raises 404 if not found."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
    return clinic


__all__ = ["get_db", "get_clinic_id", "get_clinic"]

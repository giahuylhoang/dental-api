"""v1 service catalog router — /api/services and /api/services/{id}.

Domain folder is `catalog/` to avoid colliding with the top-level
services/ package that holds business-logic services.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_authorized_clinic, get_db
from database.models import Clinic, Service

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("")
async def list_services(
    name: Optional[str] = Query(None, description="Filter by service name"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """List all services."""
    query = db.query(Service).filter(Service.clinic_id == clinic.id)
    if name:
        query = query.filter(Service.name.ilike(f"%{name}%"))
    services = query.all()
    return [{
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "duration_min": s.duration_min,
        "base_price": float(s.base_price) if s.base_price else None
    } for s in services]


@router.get("/{service_id}")
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Get service by ID."""
    service = db.query(Service).filter(Service.id == service_id, Service.clinic_id == clinic.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "duration_min": service.duration_min,
        "base_price": float(service.base_price) if service.base_price else None
    }

"""v1 providers router — /api/providers and the /api/doctors legacy alias."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Provider

router = APIRouter(prefix="/api", tags=["providers"])


@router.get("/doctors")
async def list_doctors_alias(
    db: Session = Depends(get_db), clinic: Clinic = Depends(get_clinic)
):
    """Legacy alias — frontend code that hasn't migrated to /api/providers."""
    providers = db.query(Provider).filter(Provider.clinic_id == clinic.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "title": p.title,
            "specialty": getattr(p, "specialty", None),
        }
        for p in providers
    ]


@router.get("/providers")
async def list_providers(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List all active providers."""
    providers = db.query(Provider).filter(
        Provider.clinic_id == clinic.id, Provider.is_active == True
    ).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "title": p.title,
            "specialty": p.specialty,
            "is_active": p.is_active,
        }
        for p in providers
    ]


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get provider by ID."""
    provider = db.query(Provider).filter(
        Provider.id == provider_id, Provider.clinic_id == clinic.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {
        "id": provider.id,
        "name": provider.name,
        "title": provider.title,
        "specialty": provider.specialty,
        "is_active": provider.is_active,
    }

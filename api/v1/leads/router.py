"""v1 leads router — /api/leads CRUD + status transitions."""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Lead, LeadStatus

from api.v1.leads.schemas import (
    LeadCreateRequest,
    LeadResponse,
    LeadStatusUpdateRequest,
    LeadUpdateRequest,
)

logger = logging.getLogger("dental-receptionist")

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create new lead."""
    try:
        lead_dict = lead_data.model_dump(exclude_none=True)
        lead = Lead(clinic_id=clinic.id, **lead_dict)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return LeadResponse.model_validate(lead)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {str(e)}")


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List leads with optional filters."""
    query = db.query(Lead).filter(Lead.clinic_id == clinic.id)
    if status:
        try:
            status_enum = LeadStatus(status.upper())
            query = query.filter(Lead.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if source:
        query = query.filter(Lead.source == source)
    leads = query.order_by(Lead.created_at.desc()).all()
    return [LeadResponse.model_validate(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = lead_data.model_dump(exclude_none=True)

    # Handle status update
    if "status" in update_data:
        try:
            status_enum = LeadStatus(update_data["status"].upper())
            lead.status = status_enum
            del update_data["status"]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data['status']}")

    # Update other fields
    for key, value in update_data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)

    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: str,
    request: LeadStatusUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update lead status."""
    try:
        new_status = LeadStatus(request.status.upper())
    except ValueError:
        valid_statuses = [s.value for s in LeadStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Valid values: {', '.join(valid_statuses)}"
        )

    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = new_status
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)

"""Pydantic schemas for /api/leads."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LeadCreateRequest(BaseModel):
    """Request model for creating lead."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    """Request model for updating lead."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Response model for lead."""
    id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadStatusUpdateRequest(BaseModel):
    """Request model for updating lead status."""
    status: str = Field(..., description="New status value (e.g., NEW, CONTACTED, QUALIFIED, CONVERTED, LOST)")

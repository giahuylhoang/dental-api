"""Pydantic schemas for /api/patients."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PatientCreateRequest(BaseModel):
    """Request model for creating patient."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    is_minor: Optional[bool] = False
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    consent_approved: Optional[bool] = False


class PatientResponse(BaseModel):
    """Response model for patient."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[date] = None

    class Config:
        from_attributes = True


class PatientVerifyRequest(BaseModel):
    """Request model for patient verification."""
    phone: str = Field(..., description="Phone number to verify")
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")


class PatientVerifyResponse(BaseModel):
    """Response model for patient verification."""
    patient_id: str
    verified: bool = True

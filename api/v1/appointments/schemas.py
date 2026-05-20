"""Pydantic schemas for /api/appointments."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentCreateRequest(BaseModel):
    """Request model for creating appointment."""
    start_time: str = Field(..., description="ISO datetime string")
    end_time: str = Field(..., description="ISO datetime string")
    patient_id: str
    provider_id: int
    service_id: Optional[int] = None
    patient_name: str
    service_name: str
    reason: str


class AppointmentResponse(BaseModel):
    """Response model for appointment."""
    appointment_id: str
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None
    status: str


class AppointmentStatusUpdateRequest(BaseModel):
    """Request model for updating appointment status."""
    status: str = Field(..., description="New status value (e.g., CONFIRMED, REMINDER_SENT, CANCELLED)")


class AppointmentDetailResponse(BaseModel):
    """Detailed appointment response."""
    id: str
    patient_id: str
    provider_id: int
    service_id: Optional[int] = None
    provider_name: Optional[str] = None
    service_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    reason_note: Optional[str] = None
    status: str
    calendar_event_id: Optional[str] = None

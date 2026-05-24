"""Pydantic schemas for /api/clinics."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClinicCreateRequest(BaseModel):
    """Request model for creating clinic."""
    id: str = Field(..., description="Clinic ID (e.g. clinic-a)")
    name: str = Field(..., description="Clinic display name")
    timezone: Optional[str] = Field("America/Edmonton", description="Timezone (e.g. America/Edmonton)")
    working_hour_start: Optional[int] = Field(9, description="Start of working hours (0-23)")
    working_hour_end: Optional[int] = Field(17, description="End of working hours (0-23)")
    address: Optional[str] = Field(None, description="Physical address for SMS / display")
    contact_phone: Optional[str] = Field(None, description="Clinic phone for SMS callbacks")
    booking_notification_email: Optional[str] = Field(
        None, description="Inbox to notify when a new appointment is booked"
    )


class ClinicResponse(BaseModel):
    """Response model for clinic config."""
    id: str
    name: str
    timezone: Optional[str] = None
    working_hour_start: Optional[int] = None
    working_hour_end: Optional[int] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    booking_notification_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClinicUpdateRequest(BaseModel):
    """Partial update for current clinic (X-Clinic-Id). Omit fields to leave unchanged."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    timezone: Optional[str] = None
    working_hour_start: Optional[int] = None
    working_hour_end: Optional[int] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    booking_notification_email: Optional[str] = None


class ClinicBySpecRequest(BaseModel):
    """Provision-or-update payload from the enroll_clinic.py orchestrator.

    The orchestrator owns the canonical clinic-spec.yaml; the api accepts the
    same fields and writes/updates the clinics row idempotently. Unlike
    ClinicCreateRequest, missing optional fields LEAVE existing values in place.
    """
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    timezone: Optional[str] = None
    working_hour_start: Optional[int] = None
    working_hour_end: Optional[int] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    booking_notification_email: Optional[str] = None

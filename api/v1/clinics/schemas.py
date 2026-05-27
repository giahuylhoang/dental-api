"""Pydantic schemas for /api/clinics."""
from typing import Any, Dict, List, Optional

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


class RoutingHoursWindow(BaseModel):
    open: str
    close: str


class ClinicRoutingResponse(BaseModel):
    timezone: str
    dids: List[str] = Field(default_factory=list)
    front_desk_numbers: List[str] = Field(default_factory=list)
    ring_timeout_seconds: int = 20
    hours: Dict[str, RoutingHoursWindow] = Field(default_factory=dict)
    holidays: List[str] = Field(default_factory=list)
    ai_after_hours: bool = True
    ai_in_hours_overflow: bool = True
    backup_number: Optional[str] = None
    ai_sip_uri: Optional[str] = None


class ClinicConfigResponse(BaseModel):
    id: str
    name: str
    display_name: str
    timezone: str
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    practice_type: Optional[str] = None
    assistant_name: str
    ai_disclosure_required: bool = False
    ai_disclosure_phrase: str
    greeting_message: str
    triage_questions: List[str] = Field(default_factory=list)
    pricing_preface: Optional[str] = None
    pricing_dentures_range: Optional[str] = None
    treatment_steps_guardrail: Optional[str] = None
    feature_flags: Dict[str, Any] = Field(default_factory=dict)
    general_consultation_service_id: Optional[int] = None
    knowledge_base_path: Optional[str] = None
    provider_names: List[str] = Field(default_factory=list)
    routing: ClinicRoutingResponse


class ClinicByDidResponse(BaseModel):
    clinic_id: str


class ClinicSummary(BaseModel):
    """Minimal clinic shape for list/switcher UIs.

    Intentionally omits operational + PII fields (working hours, address,
    notification email) — those belong to /clinics/me or /clinics/{id}/config."""

    id: str
    name: str
    timezone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClinicsListResponse(BaseModel):
    clinics: List[ClinicSummary]

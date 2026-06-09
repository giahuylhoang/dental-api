"""Pydantic schemas for /api/appointments."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentMutationSource(str, Enum):
    """Origin of a status-changing mutation on an appointment.

    Threaded through cancel/status/reschedule request bodies so downstream
    pipelines (e.g. the SMS reminder reply handler in Task B8) can distinguish
    inbound-call mutations from outbound-SMS-reply ones.
    """

    OUTBOUND_SMS_REPLY = "outbound_sms_reply"
    SELF_SERVICE_LINK = "self_service_link"
    INBOUND_CALL = "inbound_call"  # default for back-compat
    CLINIC_STAFF = "clinic_staff"
    SYSTEM = "system"


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
    source: AppointmentMutationSource = Field(
        default=AppointmentMutationSource.INBOUND_CALL,
        description="Origin of the mutation (used by reschedule via this schema).",
    )


class AppointmentResponse(BaseModel):
    """Response model for appointment."""
    appointment_id: str
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None
    status: str


class AppointmentStatusUpdateRequest(BaseModel):
    """Request model for updating appointment status."""
    status: str = Field(..., description="New status value (e.g., CONFIRMED, REMINDER_SENT, CANCELLED)")
    source: AppointmentMutationSource = Field(
        default=AppointmentMutationSource.INBOUND_CALL,
        description="Origin of the status change.",
    )


class AppointmentCancelRequest(BaseModel):
    """Request model for cancelling appointment. Body is optional on the wire."""
    source: AppointmentMutationSource = Field(
        default=AppointmentMutationSource.INBOUND_CALL,
        description="Origin of the cancellation.",
    )


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

"""SQLAlchemy models for the dental clinic database."""

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, DECIMAL, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database.connection import Base


class AppointmentStatus(str, PyEnum):
    """Appointment status enum."""
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    PENDING = "PENDING"
    PENDING_SYNC = "PENDING_SYNC"  # For appointments where calendar creation failed
    RESCHEDULED = "RESCHEDULED"  # Appointment was rescheduled to a new time or date
    CONFIRMED = "CONFIRMED"  # Appointment was confirmed by the user reminding them of the appointment
    REMINDER_SENT = "REMINDER_SENT"  # Appointment reminder was sent to the patient


class LeadStatus(str, PyEnum):
    """Lead status enum."""
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


DEFAULT_CLINIC_ID = "default"


class Clinic(Base):
    """Clinic model - multi-tenant config per clinic."""
    __tablename__ = "clinics"

    id = Column(String, primary_key=True, default=DEFAULT_CLINIC_ID)
    name = Column(String, nullable=False)
    display_name = Column(Text, nullable=True)
    timezone = Column(String, default="America/Edmonton")
    working_hour_start = Column(Integer, default=9)
    working_hour_end = Column(Integer, default=17)
    address = Column(Text, nullable=True)
    contact_phone = Column(String, nullable=True)
    booking_notification_email = Column(String, nullable=True)
    greeting = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="clinic")
    providers = relationship("Provider", back_populates="clinic")
    services = relationship("Service", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")
    leads = relationship("Lead", back_populates="clinic")


class Patient(Base):
    """Patient model - stores customer profile data."""
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    insurance_provider = Column(String, nullable=True)
    is_minor = Column(Boolean, default=False)
    guardian_name = Column(String, nullable=True)
    guardian_contact = Column(String, nullable=True)
    consent_approved = Column(Boolean, default=False)
    # CRM/portal columns (nullable — additive, agent's POST /api/patients unaffected)
    lead_status_crm = Column(String, nullable=True)  # 'new'/'contacted'/'booked'/'won'/'lost'/'archived'
    crm_tags = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict, server_default="{}")
    crm_notes = Column(Text, nullable=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")


class Provider(Base):
    """Provider model - generic service provider (doctor, assistant, etc.)."""
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)  # e.g. "Mr", "Dr"
    specialty = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="providers")
    appointments = relationship("Appointment", back_populates="provider")


class ProviderAvailability(Base):
    """Provider availability windows (per weekday) for scheduling slots."""
    __tablename__ = "provider_availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    # 0=Mon ... 6=Sun
    weekday = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False, default=0)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False, default=0)

    provider = relationship("Provider")


class ProviderBusyBlock(Base):
    """Busy block for a provider.

    Two storage modes (exactly one is populated on writes; enforced at the
    Pydantic layer):
    - Recurring weekly: `weekdays` is a JSON-encoded list of ints (0=Mon..6=Sun),
      optionally bounded by `recurrence_until` (inclusive).
    - Single-day one-off: `specific_date` is the calendar date.

    `weekday` is a legacy single-day field kept nullable for backward-compat reads
    on rows written before the v2 schema; writes go through `weekdays`.
    """
    __tablename__ = "provider_busy_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    # Legacy single-weekday field (0=Mon..6=Sun). Nullable; superseded by `weekdays`.
    weekday = Column(Integer, nullable=True)
    # JSON-encoded list of weekdays for recurring rules, e.g. "[0,2,4]".
    weekdays = Column(String, nullable=True)
    # Calendar date for a one-off block.
    specific_date = Column(Date, nullable=True)
    # Optional inclusive end date for the recurrence (only meaningful with `weekdays`).
    recurrence_until = Column(Date, nullable=True)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False, default=0)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False, default=0)
    label = Column(String, nullable=True)

    provider = relationship("Provider")


class Service(Base):
    """Service model - stores available services menu."""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Detailed description of the service
    duration_min = Column(Integer, nullable=True)  # Duration in minutes
    base_price = Column(DECIMAL(10, 2), nullable=True)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


class Appointment(Base):
    """Appointment model - links Patient, Provider, and Service."""
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reason_note = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID for sync
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")


class Lead(Base):
    """Lead model - stores lead information from ad campaigns."""
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    source = Column(String, nullable=True)  # Ad campaign source
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    notes = Column(Text, nullable=True)  # Qualification notes, needs, budget, timeline, etc.
    owner_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clinic = relationship("Clinic", back_populates="leads")


# v1.1 performance indexes — additive, never alter existing columns.
Index("ix_patients_clinic", Patient.clinic_id)
Index("ix_appointments_clinic_start", Appointment.clinic_id, Appointment.start_time.desc())
Index("ix_appointments_clinic_status", Appointment.clinic_id, Appointment.status)
Index("ix_appointments_patient_start", Appointment.patient_id, Appointment.start_time.desc())
Index("ix_leads_clinic_status", Lead.clinic_id, Lead.status)
Index(
    "ix_provider_busy_blocks_provider_weekday",
    ProviderBusyBlock.provider_id,
    ProviderBusyBlock.weekday,
)
Index(
    "ix_provider_availability_provider_weekday",
    ProviderAvailability.provider_id,
    ProviderAvailability.weekday,
)


class ClinicRoutingRules(Base):
    """Per-clinic agent routing config — one row per clinic."""
    __tablename__ = "clinic_routing_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, unique=True)
    rules = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict, server_default="{}")
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)


class CallLog(Base):
    """Per-call record — written by agent shutdown hook (follow-up spec), read by portal."""
    __tablename__ = "call_logs"

    id = Column(String, primary_key=True)  # LiveKit room name / call SID
    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    caller_phone = Column(String, nullable=True)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_sec = Column(Integer, nullable=True)
    outcome = Column(String, nullable=True)
    transcript = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    audio_url = Column(Text, nullable=True)
    call_metadata = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("call_logs_clinic_started_idx", "clinic_id", "started_at"),
        Index("call_logs_caller_started_idx", "caller_phone", "started_at"),
    )

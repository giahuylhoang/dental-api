"""SQLAlchemy models for the dental clinic database."""

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, DECIMAL, Index, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
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
    sms_from_number = Column(String, nullable=True)
    booking_notification_email = Column(String, nullable=True)
    # General clinic inbox (e.g. info@…). Used as an ADDITIONAL recipient for
    # clinic notifications (new bookings, referrals). Clinic-scoped so one
    # tenant's address never leaks into another's email.
    info_email = Column(String, nullable=True)
    greeting = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict, server_default="{}")
    # clinic_config_v2: shared-defaults FK + per-clinic overrides
    practice_type_id = Column(String, ForeignKey("practice_types.id"), nullable=True)
    knowledge_base_path = Column(String, nullable=True)
    # use_alter=True breaks the clinics<->services FK cycle so SQLAlchemy can
    # sort tables for create_all; the actual FK is emitted post-creation via
    # ALTER TABLE on Postgres (and elided on SQLite, which doesn't support
    # ALTER TABLE ADD FOREIGN KEY anyway).
    general_consultation_service_id = Column(
        Integer,
        ForeignKey("services.id", use_alter=True, name="fk_clinics_general_consultation_service_id"),
        nullable=True,
    )
    feature_flags_overrides = Column(JSON, nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="clinic")
    providers = relationship("Provider", back_populates="clinic")
    services = relationship("Service", back_populates="clinic", foreign_keys="Service.clinic_id")
    appointments = relationship("Appointment", back_populates="clinic")
    leads = relationship("Lead", back_populates="clinic")
    practice_type = relationship("PracticeType", lazy="joined")
    # ``routing`` uses lazy="select" (not "joined") because clinic_routing is a
    # Postgres-only table (TEXT[] + JSONB), skipped on SQLite test runs via
    # _SQLITE_SKIP_TABLES. An eager JOIN would fire on every Clinic load and
    # crash SQLite-backed tests with "no such table: clinic_routing". Callers
    # that need routing should query it explicitly (or .selectinload()).
    routing = relationship(
        "ClinicRouting",
        uselist=False,
        cascade="all, delete-orphan",
        back_populates="clinic",
    )


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
    # Disambiguate: Clinic now has TWO FKs to Service (services.clinic_id and
    # clinics.general_consultation_service_id from clinic_config_v2). Pin this
    # relationship to the services.clinic_id side.
    clinic = relationship("Clinic", back_populates="services", foreign_keys=[clinic_id])
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
    hold_expiry_at = Column(DateTime, nullable=True)  # set for PENDING web/voice holds; naive UTC
    patient_confirmed = Column(Boolean, nullable=False, default=False)  # web self-confirm flag
    source = Column(String, nullable=True)  # 'booking-web-hold' | 'voice-hold' | None (staff/direct)
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


class PracticeType(Base):
    """Shared defaults for a class of practice (denturist, dentist, ...).

    Many clinics may share one practice_type row; the merged config is
    practice_type ← clinic columns ← per-clinic override tables.
    """
    __tablename__ = "practice_types"

    id = Column(String, primary_key=True)
    assistant_name = Column(String, nullable=False)
    ai_disclosure_required = Column(Boolean, nullable=False, default=True, server_default="true")
    ai_disclosure_phrase = Column(Text, nullable=False)
    greeting_message = Column(Text, nullable=False)
    pricing_preface = Column(Text, nullable=False)
    pricing_dentures_range = Column(Text, nullable=True)
    treatment_steps_guardrail = Column(Text, nullable=False)
    triage_questions = Column(JSON, nullable=False, default=list, server_default="[]")
    default_feature_flags = Column(JSON, nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ClinicRouting(Base):
    """Per-clinic routing/telephony config.

    dids and front_desk_numbers are TEXT[] (Postgres-native arrays);
    hours is a single JSONB column shaped like {"mon": {"open":..., "close":...}, ...}.
    The GIN index on dids powers the by-did reverse lookup.
    """
    __tablename__ = "clinic_routing"

    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), primary_key=True)
    ring_timeout_seconds = Column(Integer, nullable=False, default=20, server_default="20")
    ai_after_hours = Column(Boolean, nullable=False, default=True, server_default="true")
    ai_in_hours_overflow = Column(Boolean, nullable=False, default=True, server_default="true")
    backup_number = Column(String, nullable=True)
    ai_sip_uri = Column(String, nullable=True)
    dids = Column(ARRAY(Text), nullable=False, default=list, server_default="{}")
    front_desk_numbers = Column(ARRAY(Text), nullable=False, default=list, server_default="{}")
    hours = Column(JSONB, nullable=False, default=dict, server_default="{}")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    clinic = relationship("Clinic", back_populates="routing")


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


# ---------------------------------------------------------------------------
# Re-exports — convenience for callers that resolve clinic config end-to-end.
#
# These tables physically live in database.ops.ai_config (AI Receptionist
# config) and database.v1_1.models (v1.1 polish: hours/closures/etc.). The
# clinic_config_v2 resolver merges them with PracticeType + ClinicRouting +
# Clinic, so it's cleaner for one import site (database.models) to expose
# every model the resolver touches than to scatter the imports.
# ---------------------------------------------------------------------------
from database.ops.ai_config import ClinicAiVoice, ClinicAiDisclosure  # noqa: E402,F401
from database.v1_1.models import ClinicClosure  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Referrals (public referral form) — Phase 1.
# Files live in object storage (GCS in prod); rows below carry metadata only.
# Kept OUT of the shared `documents` table so the clinical-documents contract
# (NOT NULL patient_id / content_sha256) is untouched. Phase 2 conversion
# promotes a referral_documents row into `documents` with patient_id set.
# All columns are SQLite-compatible, so these create cleanly in the test DB.
# ---------------------------------------------------------------------------
class ReferralStatus(str, PyEnum):
    NEW = "NEW"            # created; awaiting file uploads / completion
    READY = "READY"        # files uploaded + recorded; clinic notified
    IN_REVIEW = "IN_REVIEW"
    CONVERTED = "CONVERTED"  # promoted to a patient (Phase 2)
    ARCHIVED = "ARCHIVED"


class Referral(Base):
    """A patient referral submitted by an external clinic via the public form."""
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    patient_name = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    referred_by = Column(String, nullable=False)            # referring clinic name
    referrer_contact = Column(String, nullable=True)        # optional email/phone
    proposed_extraction_date = Column(Date, nullable=True)
    tx_plan = Column(Text, nullable=True)                   # treatment-plan notes
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)  # null = "Either"
    status = Column(SQLEnum(ReferralStatus), nullable=False, default=ReferralStatus.NEW)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)     # set on Phase-2 conversion
    source = Column(String, nullable=False, default="public-referral")
    submit_ip = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship(
        "ReferralDocument", back_populates="referral", cascade="all, delete-orphan",
    )


class ReferralDocument(Base):
    """A file attached to a referral. Bytes live in object storage (storage_url)."""
    __tablename__ = "referral_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, default=DEFAULT_CLINIC_ID)
    referral_id = Column(String, ForeignKey("referrals.id"), nullable=False)
    kind = Column(String, nullable=False, default="xray")   # xray|photo|pdf|other
    storage_url = Column(Text, nullable=False)              # object key in the bucket
    storage_backend = Column(String, nullable=False, default="gcs")  # 'gcs'|'local'
    mime = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    sha256 = Column(String, nullable=True)                  # optional for GCS-origin files
    original_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    referral = relationship("Referral", back_populates="documents")


Index("ix_referrals_clinic_status_created", Referral.clinic_id, Referral.status, Referral.created_at.desc())
Index("ix_referral_documents_referral", ReferralDocument.clinic_id, ReferralDocument.referral_id)

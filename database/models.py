"""SQLAlchemy models for the dental clinic database."""

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
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
    timezone = Column(String, default="America/Edmonton")
    working_hour_start = Column(Integer, default=9)
    working_hour_end = Column(Integer, default=17)
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
    """Recurring busy block for a provider (weekday/time window)."""
    __tablename__ = "provider_busy_blocks"

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clinic = relationship("Clinic", back_populates="leads")

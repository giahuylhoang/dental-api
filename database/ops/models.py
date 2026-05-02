"""ORM models for Track 3: Scheduling, Billing, Insurance, Communications, CRM."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, DECIMAL, JSON, Float,
)
from sqlalchemy.orm import relationship

from database.connection import Base


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

class Operatory(Base):
    __tablename__ = "operatories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    name = Column(String, nullable=False)
    equipment_tags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)


class AppointmentResource(Base):
    __tablename__ = "appointment_resources"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=False)
    operatory_id = Column(String, ForeignKey("operatories.id"), nullable=False)


class AppointmentRecurrence(Base):
    __tablename__ = "appointment_recurrences"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    parent_appointment_id = Column(String, ForeignKey("appointments.id"), nullable=False)
    rule = Column(Text, nullable=False)  # RRULE string
    generated_through_date = Column(DateTime, nullable=True)


class AppointmentReminder(Base):
    __tablename__ = "appointment_reminders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=False)
    channel = Column(String, nullable=False)  # sms|email
    offset_minutes = Column(Integer, nullable=False)  # minutes before appointment
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending|sent|failed|cancelled
    failure_reason = Column(Text, nullable=True)


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    requested_window_start = Column(DateTime, nullable=False)
    requested_window_end = Column(DateTime, nullable=False)
    provider_pref = Column(Integer, ForeignKey("providers.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    priority = Column(Integer, default=0)
    status = Column(String, default="open")  # open|filled|expired|cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Recall
# ---------------------------------------------------------------------------

class RecallRule(Base):
    __tablename__ = "recall_rules"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    name = Column(String, nullable=False)
    trigger_event = Column(String, nullable=False)  # denture_delivered|reline|annual|custom
    offset_days = Column(Integer, nullable=False)
    channel = Column(String, default="sms")  # sms|email|both


class Recall(Base):
    __tablename__ = "recalls"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    rule_id = Column(String, ForeignKey("recall_rules.id"), nullable=False)
    due_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending|sent|completed|cancelled


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=True)
    treatment_plan_id = Column(String, nullable=True)  # FK to treatment_plans if present
    status = Column(String, default="draft")  # draft|issued|partial|paid|void
    subtotal = Column(DECIMAL(10, 2), default=0)
    gst = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), default=0)
    balance = Column(DECIMAL(10, 2), default=0)
    issued_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    currency = Column(String, default="CAD")
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    sequence = Column(Integer, default=1)
    procedure_code = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    qty = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="lines")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    method = Column(String, nullable=False)  # cash|card|cheque|etransfer|insurance
    amount = Column(DECIMAL(10, 2), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")


# ---------------------------------------------------------------------------
# Insurance
# ---------------------------------------------------------------------------

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    carrier = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # predetermination|claim
    assignment_of_benefits = Column(Boolean, default=False)
    status = Column(String, default="draft")  # draft|submitted|accepted|adjudicated|paid|rejected|partial
    submitted_at = Column(DateTime, nullable=True)
    adjudicated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    response_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("ClaimEvent", back_populates="claim", cascade="all, delete-orphan")


class ClaimEvent(Base):
    __tablename__ = "claim_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String, ForeignKey("insurance_claims.id"), nullable=False)
    kind = Column(String, nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, nullable=True)

    claim = relationship("InsuranceClaim", back_populates="events")


# ---------------------------------------------------------------------------
# Communications
# ---------------------------------------------------------------------------

class Communication(Base):
    __tablename__ = "communications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    channel = Column(String, nullable=False)  # sms|email|inbound_sms|inbound_email
    direction = Column(String, nullable=False)  # out|in
    body = Column(Text, nullable=False)
    status = Column(String, default="queued")  # queued|sent|delivered|failed|received
    related_appointment_id = Column(String, ForeignKey("appointments.id"), nullable=True)
    related_invoice_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    name = Column(String, nullable=False)
    audience_query = Column(JSON, nullable=True)
    schedule_at = Column(DateTime, nullable=True)
    channel = Column(String, nullable=False)  # sms|email
    body_template = Column(Text, nullable=False)
    status = Column(String, default="draft")  # draft|scheduled|sending|sent|cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# CRM
# ---------------------------------------------------------------------------

class LeadEvent(Base):
    __tablename__ = "lead_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False)
    kind = Column(String, nullable=False)  # note|status_change|email_sent|sms_sent|converted
    occurred_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, nullable=True)

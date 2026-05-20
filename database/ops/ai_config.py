"""
AI Receptionist configuration models — additive-only.

Four tables, all scoped by clinic_id. Registered with the same Base via
database/ops/__init__.py so Base.metadata.create_all picks them up.

These tables back the Settings → Voice & Persona / AI Disclosure /
Services-bookable / Knowledge tabs in the Next.js frontend. They never alter
the v1 schema (database/models.py) — the calendar_client contract is preserved.
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, Index,
)

from database.connection import Base


class ClinicAiVoice(Base):
    """Per-clinic AI Receptionist voice/persona row.

    One row per clinic. First read auto-creates with defaults from
    the design-system prototype (admin-voice.html).
    """
    __tablename__ = "clinic_ai_voice"

    clinic_id = Column(String, ForeignKey("clinics.id"), primary_key=True)
    assistant_name = Column(String, nullable=False, default="Dental AI")
    provider_title = Column(String, nullable=False, default="Denturist")
    reason_question = Column(String, nullable=False, default="What brings you in?")
    language = Column(String, nullable=False, default="en-US")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClinicAiDisclosure(Base):
    """Per-clinic AI disclosure row.

    `last_reviewed_at` is bumped only when the phrase content changes,
    so toggling `required` does not look like a content review.
    """
    __tablename__ = "clinic_ai_disclosure"

    clinic_id = Column(String, ForeignKey("clinics.id"), primary_key=True)
    required = Column(Boolean, nullable=False, default=False)
    phrase = Column(Text, nullable=False, default="")
    last_reviewed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceAiBookable(Base):
    """One row per (clinic, service) declaring whether the AI is allowed
    to book this service over the phone. Default semantics (no row → false)
    are encoded in the API layer's join."""
    __tablename__ = "service_ai_bookable"

    service_id = Column(Integer, ForeignKey("services.id"), primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    bookable = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClinicKnowledgeDoc(Base):
    """Markdown knowledge base file the AI can reference.
    `filename` unique per clinic (not globally)."""
    __tablename__ = "clinic_knowledge_doc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False, default="")
    word_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "filename", name="uq_knowledge_clinic_filename"),
    )


# Indexes
Index("ix_service_ai_bookable_clinic", ServiceAiBookable.clinic_id)
Index("ix_clinic_knowledge_doc_clinic", ClinicKnowledgeDoc.clinic_id)

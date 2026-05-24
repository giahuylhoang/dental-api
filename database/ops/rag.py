"""SQLAlchemy models for the Clinic Q&A RAG feature.

Two tables, both scoped by clinic_id:
  - clinic_faqs:  hot tier, rendered into the voice-agent system prompt.
  - rag_docs:     cold tier, retrieved on-demand via embedding similarity.

Vector column uses pgvector. SQLite (used elsewhere in tests) cannot host this
schema — pgvector tests opt in via the `pgvector` marker.
"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from database.connection import Base


class ClinicFaq(Base):
    __tablename__ = "clinic_faqs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    ordering = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_clinic_faqs_by_clinic", "clinic_id", "ordering"),
    )


class RagDoc(Base):
    __tablename__ = "rag_docs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    doc_title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    voice_ready = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    doc_metadata = Column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_rag_docs_by_clinic", "clinic_id"),
    )

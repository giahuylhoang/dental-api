"""Clinical ORM models for Track 2."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    Integer, JSON, UniqueConstraint, Float, Index,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def _uuid():
    return str(uuid.uuid4())


class PatientMedicalHistory(Base):
    __tablename__ = "patient_medical_history"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    conditions = Column(JSON, default=list)          # [{name, since, severity}]
    bisphosphonates_use = Column(Boolean, default=False)
    allergies_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientCommunicationPreference(Base):
    """v1.1 — channel-level opt-in / opt-out per patient (CASL/PIPEDA).

    Notification helpers (clients/sms_client.py, clients/email_client.py, the
    reminder scheduler) MUST consult this table before dispatching. Absence of
    a row for a channel means "no preference set" — default behavior is opted-in
    so existing flows are not silently broken.
    """
    __tablename__ = "patient_communication_preferences"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    channel = Column(String, nullable=False)         # sms|email|phone|mail
    opted_in = Column(Boolean, default=True, nullable=False)
    language = Column(String, default="en", nullable=False)  # en|fr
    do_not_contact_until = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "patient_id", "channel", name="ux_pcp_clinic_patient_channel"),
    )


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    name = Column(String, nullable=False)
    reaction = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientMedication(Base):
    __tablename__ = "patient_medications"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    name = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    since = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientInsurance(Base):
    __tablename__ = "patient_insurance"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    carrier = Column(String, nullable=False)
    policy_number = Column(String, nullable=True)
    group_number = Column(String, nullable=True)
    holder_name = Column(String, nullable=True)
    holder_relationship = Column(String, nullable=True)
    assignment_of_benefits = Column(Boolean, default=False)
    coverage_pct_by_category = Column(JSON, default=dict)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientConsent(Base):
    __tablename__ = "patient_consent"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    form_kind = Column(String, nullable=False)
    form_version = Column(String, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    signature_blob_url = Column(Text, nullable=True)
    witness_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    kind = Column(String, nullable=False)           # photo|xray|consent|other
    storage_url = Column(Text, nullable=False)
    storage_backend = Column(String, nullable=False, default="gcs")  # 'gcs'|'local'
    original_name = Column(String, nullable=True)
    content_sha256 = Column(String, nullable=False)
    mime = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "clinic_id", "patient_id", "content_sha256",
            name="uq_doc_clinic_patient_sha",
        ),
    )


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(String, nullable=True)
    author_id = Column(String, nullable=True)
    soap_subjective = Column(Text, nullable=True)
    soap_objective = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)
    soap_plan = Column(Text, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    supersedes_id = Column(String, ForeignKey("clinical_notes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientNote(Base):
    """Free-text CRM note attached to a patient (append-style, editable/deletable).

    Distinct from ClinicalNote (which is SOAP-structured, appointment-linked and
    lockable). This is the lightweight "who said what when" CRM jot.
    """
    __tablename__ = "patient_notes"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    author_id = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DentureCase(Base):
    __tablename__ = "denture_cases"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    arch = Column(String, nullable=False)           # upper|lower|both
    case_type = Column(String, nullable=False)      # complete|partial|immediate|implant_retained
    current_stage = Column(String, default="consult")
    status = Column(String, default="open")         # open|closed
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("DentureCaseEvent", back_populates="case", cascade="all, delete-orphan")


class DentureCaseEvent(Base):
    __tablename__ = "denture_case_events"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("denture_cases.id"), nullable=False)
    stage = Column(String, nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    provider_id = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    photo_document_ids = Column(JSON, default=list)

    case = relationship("DentureCase", back_populates="events")


class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    status = Column(String, default="draft")        # draft|presented|accepted|in_progress|completed|declined
    total_estimate = Column(Float, default=0.0)
    insurance_estimate = Column(Float, default=0.0)
    patient_estimate = Column(Float, default=0.0)
    presented_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("TreatmentPlanItem", back_populates="plan", cascade="all, delete-orphan",
                         order_by="TreatmentPlanItem.sequence")


class TreatmentPlanItem(Base):
    __tablename__ = "treatment_plan_items"

    id = Column(String, primary_key=True, default=_uuid)
    plan_id = Column(String, ForeignKey("treatment_plans.id"), nullable=False)
    sequence = Column(Integer, default=0)
    procedure_code = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    fee = Column(Float, default=0.0)
    insurance_coverage_pct = Column(Float, default=0.0)
    tooth_number = Column(Integer, nullable=True)
    care_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    plan = relationship("TreatmentPlan", back_populates="items")


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    default_duration_min = Column(Integer, nullable=True)
    default_fee = Column(Float, default=0.0)
    category = Column(String, default="other")      # preventive|diagnostic|restorative|prosthodontic|periodontic|surgical|other

    __table_args__ = (UniqueConstraint("clinic_id", "code", name="uq_procedure_clinic_code"),)


class LabVendor(Base):
    __tablename__ = "lab_vendors"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    sla_days = Column(Integer, nullable=True)
    price_list = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("LabCase", back_populates="vendor")


class LabCase(Base):
    __tablename__ = "lab_cases"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    denture_case_id = Column(String, ForeignKey("denture_cases.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("lab_vendors.id"), nullable=False)
    case_number = Column(Text, nullable=True, unique=True)
    treatment_plan_id = Column(String, ForeignKey("treatment_plans.id"), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    due_back_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String, default="draft")        # draft|sent|in_progress|returned|remake|cancelled
    remake_of_id = Column(String, ForeignKey("lab_cases.id"), nullable=True)
    remake_reason = Column(Text, nullable=True)
    lab_fee = Column(Float, nullable=True)
    courier_tracking = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("LabVendor", back_populates="cases")
    events = relationship("LabCaseEvent", back_populates="lab_case", cascade="all, delete-orphan")


class LabCaseEvent(Base):
    __tablename__ = "lab_case_events"

    id = Column(String, primary_key=True, default=_uuid)
    lab_case_id = Column(String, ForeignKey("lab_cases.id"), nullable=False)
    kind = Column(String, nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, default=dict)

    lab_case = relationship("LabCase", back_populates="events")


# v1.1 indexes
Index("ix_clinical_notes_patient_created", ClinicalNote.patient_id, ClinicalNote.created_at.desc())
Index("ix_clinical_notes_appointment", ClinicalNote.appointment_id)
Index("ix_denture_cases_patient_status", DentureCase.patient_id, DentureCase.status)
Index("ix_denture_cases_clinic_status", DentureCase.clinic_id, DentureCase.status)
Index("ix_lab_cases_clinic_status", LabCase.clinic_id, LabCase.status)
Index("ix_lab_cases_denture_case", LabCase.denture_case_id)
Index("ix_treatment_plans_patient_status", TreatmentPlan.patient_id, TreatmentPlan.status)
Index("ix_documents_patient_kind", Document.patient_id, Document.kind)
Index("ix_patient_insurance_patient_primary", PatientInsurance.patient_id, PatientInsurance.is_primary)
Index(
    "ix_patient_notes_clinic_patient_created",
    PatientNote.clinic_id, PatientNote.patient_id, PatientNote.created_at,
)

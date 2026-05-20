"""v1.1 ORM models — denturist polish (purely additive).

Tables in this module have no foreign-key dependencies into one another that
violate referential integrity with existing v1 tables. They reference
`patients`, `clinics`, `providers`, `denture_cases`, `lab_cases`,
`insurance_claims`, `recall_rules`, etc. by FK without modifying those tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    JSON, UniqueConstraint, Index, DECIMAL, Date, Time,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Patient lifecycle status (v1.1)
# ---------------------------------------------------------------------------
#
# Use case: a phone-booking patient gives only name + phone. They land in
# `pending` and are auto-promoted to `active` once consent + DOB + insurance
# are captured. Sibling table — v1 `patients` rows stay untouched.
#
# Status values:
#   pending   — quick-booked; missing identifying / consent fields
#   active    — fully registered, can be billed
#   inactive  — opted out / soft-archived
#   deceased  — record retained for billing / family history
#   merged    — duplicate; record kept for FK integrity but pointer in `notes`
#               or audit log links to surviving patient
#
# Default behavior when NO row exists: read as `active`. This preserves v1
# semantics (every existing patient was effectively active before this table
# existed) so backfill is optional, not load-bearing.

PATIENT_STATUSES = ("pending", "active", "inactive", "deceased", "merged")


class PatientLifecycle(Base):
    __tablename__ = "patient_lifecycle"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    registered_at = Column(DateTime, nullable=True)         # set when status -> active
    last_status_change_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        # One lifecycle row per patient.
        UniqueConstraint("patient_id", name="ux_patient_lifecycle_patient"),
    )


# ---------------------------------------------------------------------------
# Tier 2a — Per-weekday clinic hours + closures
# ---------------------------------------------------------------------------

class ClinicOperatingHours(Base):
    """One row per (clinic, weekday). Replaces global Clinic.working_hour_*
    going forward. The legacy columns remain populated for backwards compat;
    slot computation falls through to them when no rows exist for a clinic."""
    __tablename__ = "clinic_operating_hours"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon ... 6=Sun
    open_at = Column(Time, nullable=False)
    close_at = Column(Time, nullable=False)
    lunch_start = Column(Time, nullable=True)
    lunch_end = Column(Time, nullable=True)
    is_closed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "day_of_week", name="ux_clinic_hours_clinic_dow"),
    )


class ClinicClosure(Base):
    """One-off closures (statutory holidays, training days, emergencies)."""
    __tablename__ = "clinic_closures"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null = single day
    kind = Column(String, nullable=False)   # holiday|training|emergency|other
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Tier 2b — Provider one-off time-off
# ---------------------------------------------------------------------------

class ProviderTimeOff(Base):
    """One-off provider unavailability (vacations, sick days, etc.).
    Combined with the recurring ProviderBusyBlock and ProviderAvailability
    tables for slot computation."""
    __tablename__ = "provider_time_off"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)  # vacation|sick|admin|training|jury_duty|other
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Tier 2c — Tooth chart / odontogram
# ---------------------------------------------------------------------------

class ToothChartEntry(Base):
    """Per-tooth status snapshot. ISO universal numbering 1–32 (adult). One
    row per tooth per patient; mutate as exam findings change."""
    __tablename__ = "tooth_chart_entries"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    tooth_number = Column(Integer, nullable=False)  # 1..32 ISO
    # status ∈ present|missing|extracted|implant|bridge_pontic|crowned|filled|root_treated|to_extract
    status = Column(String, nullable=False)
    surface_notes = Column(JSON, nullable=True)  # {mesial, distal, occlusal, buccal, lingual: notes}
    last_examined_at = Column(DateTime, nullable=True)
    examined_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "patient_id", "tooth_number",
                         name="ux_tooth_chart_clinic_patient_tooth"),
    )


# ---------------------------------------------------------------------------
# Tier 2d — Implant detail per denture case
# ---------------------------------------------------------------------------

class DentureCaseImplant(Base):
    """One row per implant within an implant-retained denture case. Required
    for biocompatibility recall sweeps (vendor + lot)."""
    __tablename__ = "denture_case_implants"

    id = Column(String, primary_key=True, default=_uuid)
    denture_case_id = Column(String, ForeignKey("denture_cases.id"), nullable=False, index=True)
    tooth_position = Column(Integer, nullable=False)  # 1..32 ISO
    vendor = Column(String, nullable=False)
    model = Column(String, nullable=True)
    lot_number = Column(String, nullable=False, index=True)  # indexed for recall sweeps
    surface_treatment = Column(String, nullable=True)  # machined|SLA|RaSah|TiUnite|other
    abutment_type = Column(String, nullable=True)     # ball|bar|locator|magnet|other
    placed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Tier 2e — Patient relationships (FK guardians)
# ---------------------------------------------------------------------------

class PatientRelationship(Base):
    """Structured side of patient.guardian_name/guardian_contact (which stay).
    Allows linking a patient to another patient (e.g. parent of minor)."""
    __tablename__ = "patient_relationships"

    id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    related_patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    # parent|spouse|child|dependent|emergency_contact|sibling|other
    relationship = Column(String, nullable=False)
    is_primary_guardian = Column(Boolean, default=False, nullable=False)
    authority = Column(String, default="contact_only", nullable=False)  # full|limited|contact_only
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("patient_id", "related_patient_id", "relationship",
                         name="ux_relationship_patient_related_kind"),
    )


# ---------------------------------------------------------------------------
# Tier 2f — Human-readable identifiers (clinic-scoped sequences)
# ---------------------------------------------------------------------------

class ClinicSequence(Base):
    """Per-(clinic, kind, year) monotonic counter used to mint MRNs, invoice
    numbers, and claim numbers. Use SELECT ... FOR UPDATE on Postgres for
    correctness; SQLite is single-writer so no locking needed."""
    __tablename__ = "clinic_sequences"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    sequence_kind = Column(String, nullable=False)  # patient_mrn|invoice|claim
    year = Column(Integer, nullable=False)
    next_value = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "sequence_kind", "year",
                         name="ux_clinic_sequence_clinic_kind_year"),
    )


class HumanIdentifier(Base):
    """Human-readable identifiers for v1 entities — kept in a sibling table so
    that no existing class needs a new column. v2 endpoints join here to
    expose `mrn`, `invoice_number`, `claim_number` etc. without changing v1
    response shapes.

    `entity_type` ∈ {patient, invoice, claim} and is intentionally a string
    rather than an enum to allow future kinds without a migration.
    """
    __tablename__ = "human_identifiers"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    entity_type = Column(String, nullable=False)   # patient|invoice|claim
    entity_id = Column(String, nullable=False)
    kind = Column(String, nullable=False)          # mrn|invoice_number|claim_number
    value = Column(String, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # One identifier of a given kind per entity.
        UniqueConstraint("entity_type", "entity_id", "kind", name="ux_humanid_entity_kind"),
        # Identifiers must be unique per (clinic, kind) — i.e. no two patients
        # in the same clinic share an MRN, no two invoices share a number.
        UniqueConstraint("clinic_id", "kind", "value", name="ux_humanid_clinic_kind_value"),
    )


# ---------------------------------------------------------------------------
# Tier 2g — Provider compensation history
# ---------------------------------------------------------------------------

class ProviderCompensationHistory(Base):
    """Audit trail for provider contract / commission rate changes. The
    current values are denormalized onto `providers.contract_type` and
    `providers.commission_rate` (added via migration)."""
    __tablename__ = "provider_compensation_history"

    id = Column(String, primary_key=True, default=_uuid)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    effective_date = Column(Date, nullable=False)
    contract_type = Column(String, nullable=False)  # employee_salary|independent_contractor|commission_percent
    commission_rate = Column(DECIMAL(5, 4), nullable=True)  # e.g. 0.3000 = 30%
    notes = Column(Text, nullable=True)
    set_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Tier 2h — Inventory: items, lots, per-lab-case consumption
# ---------------------------------------------------------------------------

class InventoryItem(Base):
    """Master catalog entry — a stock-keepable material a clinic uses."""
    __tablename__ = "inventory_items"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    # acrylic|impression_material|teeth_set|liner|reline_material|wax|model_stone|other
    category = Column(String, nullable=False)
    unit = Column(String, nullable=False)            # kg|g|ml|each|set
    supplier = Column(String, nullable=True)
    reorder_threshold = Column(DECIMAL(12, 4), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("clinic_id", "sku", name="ux_inventory_item_clinic_sku"),
    )


class InventoryLot(Base):
    """One physical received batch of an item — manufacturer lot number,
    expiry, quantity on hand. Indexed on lot_number for vendor-recall sweeps."""
    __tablename__ = "inventory_lots"

    id = Column(String, primary_key=True, default=_uuid)
    item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False, index=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False, index=True)
    lot_number = Column(String, nullable=False, index=True)
    expiry_date = Column(Date, nullable=True)
    qty_received = Column(DECIMAL(12, 4), nullable=False)
    qty_on_hand = Column(DECIMAL(12, 4), nullable=False)
    supplier_batch_id = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    quarantined_at = Column(DateTime, nullable=True)
    quarantine_reason = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("item_id", "lot_number", name="ux_inventory_lot_item_lotno"),
    )


class LabCaseMaterial(Base):
    """How much of which lot was consumed by which lab case. Drives
    cost-of-goods reporting and biocompatibility recall traceability."""
    __tablename__ = "lab_case_materials"

    id = Column(String, primary_key=True, default=_uuid)
    lab_case_id = Column(String, ForeignKey("lab_cases.id"), nullable=False, index=True)
    item_id = Column(String, ForeignKey("inventory_items.id"), nullable=False)
    lot_id = Column(String, ForeignKey("inventory_lots.id"), nullable=False, index=True)
    qty_consumed = Column(DECIMAL(12, 4), nullable=False)
    unit_cost = Column(DECIMAL(12, 4), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Tier 2i — Structured CDAnet claim response codes
# ---------------------------------------------------------------------------

class ClaimResponseCode(Base):
    """One row per response code returned for a claim. Lives alongside the
    untyped `insurance_claims.response_payload` JSON; this table is the
    queryable / dashboardable side."""
    __tablename__ = "claim_response_codes"

    id = Column(String, primary_key=True, default=_uuid)
    claim_id = Column(String, ForeignKey("insurance_claims.id"), nullable=False, index=True)
    code = Column(String, nullable=False)         # CDAnet response code
    description = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    affected_service_codes = Column(JSON, nullable=True)
    severity = Column(String, default="info", nullable=False)  # info|warn|error
    occurred_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# v1.1 secondary indexes (declared at module level)
# ---------------------------------------------------------------------------

Index("ix_clinic_closures_clinic_start", ClinicClosure.clinic_id, ClinicClosure.start_date)
Index("ix_provider_time_off_provider_range", ProviderTimeOff.provider_id, ProviderTimeOff.start_at, ProviderTimeOff.end_at)
Index("ix_provider_compensation_history_provider_eff", ProviderCompensationHistory.provider_id, ProviderCompensationHistory.effective_date.desc())
Index("ix_inventory_lots_clinic_qty", InventoryLot.clinic_id, InventoryLot.qty_on_hand)
Index("ix_claim_response_codes_claim_severity", ClaimResponseCode.claim_id, ClaimResponseCode.severity)
Index("ix_clinic_sequences_clinic_kind", ClinicSequence.clinic_id, ClinicSequence.sequence_kind)
Index("ix_human_identifiers_entity", HumanIdentifier.entity_type, HumanIdentifier.entity_id)
Index("ix_human_identifiers_clinic_kind", HumanIdentifier.clinic_id, HumanIdentifier.kind)
Index("ix_patient_lifecycle_clinic_status", PatientLifecycle.clinic_id, PatientLifecycle.status)

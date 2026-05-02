"""
Sequence allocator for human-readable identifiers (MRN, invoice number,
claim number).

Each clinic gets its own monotonic counter per (kind, year). On Postgres we
use SELECT ... FOR UPDATE to prevent concurrent double-allocation; SQLite is
single-writer so a plain UPDATE is sufficient.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.v1_1.models import ClinicSequence, HumanIdentifier


def _next_value(db: Session, clinic_id: str, kind: str, year: int) -> int:
    is_postgres = db.bind and db.bind.dialect.name == "postgresql"
    q = db.query(ClinicSequence).filter_by(
        clinic_id=clinic_id, sequence_kind=kind, year=year
    )
    if is_postgres:
        q = q.with_for_update()
    row = q.first()
    if row is None:
        row = ClinicSequence(
            clinic_id=clinic_id, sequence_kind=kind, year=year, next_value=1
        )
        db.add(row)
        db.flush()
    value = row.next_value
    row.next_value = value + 1
    row.updated_at = datetime.utcnow()
    db.flush()
    return value


def mint_mrn(
    db: Session,
    clinic_id: str,
    patient_id: str,
    last_name: Optional[str],
    year: Optional[int] = None,
) -> str:
    """Allocate and persist a `mrn` HumanIdentifier for `patient_id`. Idempotent:
    if one already exists, return it."""
    existing = (
        db.query(HumanIdentifier)
        .filter_by(entity_type="patient", entity_id=patient_id, kind="mrn")
        .first()
    )
    if existing:
        return existing.value
    yr = year or datetime.utcnow().year
    seq = _next_value(db, clinic_id, "patient_mrn", yr)
    last = (last_name or "X").upper().replace(" ", "")[:10] or "X"
    value = f"{last}-{yr}-{seq:04d}"
    db.add(HumanIdentifier(
        clinic_id=clinic_id, entity_type="patient", entity_id=patient_id,
        kind="mrn", value=value,
    ))
    db.flush()
    return value


def mint_invoice_number(
    db: Session,
    clinic_id: str,
    invoice_id: str,
    year: Optional[int] = None,
) -> str:
    existing = (
        db.query(HumanIdentifier)
        .filter_by(entity_type="invoice", entity_id=invoice_id, kind="invoice_number")
        .first()
    )
    if existing:
        return existing.value
    yr = year or datetime.utcnow().year
    seq = _next_value(db, clinic_id, "invoice", yr)
    value = f"INV-{yr}-{seq:06d}"
    db.add(HumanIdentifier(
        clinic_id=clinic_id, entity_type="invoice", entity_id=invoice_id,
        kind="invoice_number", value=value,
    ))
    db.flush()
    return value


def mint_claim_number(
    db: Session,
    clinic_id: str,
    claim_id: str,
    year: Optional[int] = None,
) -> str:
    existing = (
        db.query(HumanIdentifier)
        .filter_by(entity_type="claim", entity_id=claim_id, kind="claim_number")
        .first()
    )
    if existing:
        return existing.value
    yr = year or datetime.utcnow().year
    seq = _next_value(db, clinic_id, "claim", yr)
    value = f"CLM-{yr}-{seq:06d}"
    db.add(HumanIdentifier(
        clinic_id=clinic_id, entity_type="claim", entity_id=claim_id,
        kind="claim_number", value=value,
    ))
    db.flush()
    return value


def lookup(
    db: Session,
    entity_type: str,
    entity_id: str,
    kind: str,
) -> Optional[str]:
    row = (
        db.query(HumanIdentifier)
        .filter_by(entity_type=entity_type, entity_id=entity_id, kind=kind)
        .first()
    )
    return row.value if row else None

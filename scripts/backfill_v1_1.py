"""
Idempotent backfill for v1.1 schema polish.

Runs after `alembic upgrade head` to populate derived data on existing rows:
  1. MRNs for every patient.
  2. Invoice numbers for every issued/partial/paid invoice.
  3. Claim numbers for every submitted+ claim.
  4. Default ClinicOperatingHours rows from each clinic's legacy
     working_hour_start/end (Mon-Fri only) when no rows exist.
  5. Default PatientCommunicationPreference (sms, opted_in=true) for every
     patient with a non-empty phone.

Re-running is safe — every step checks for existing rows first.

Usage:
    DATABASE_URL=sqlite:///./dental_clinic.db uv run python scripts/backfill_v1_1.py
"""
from __future__ import annotations

import os
import sys
from datetime import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime

from database.connection import SessionLocal
from database.models import Clinic, Patient
from database.clinical.models import PatientCommunicationPreference
from database.ops.models import Invoice, InsuranceClaim
from database.v1_1.models import ClinicOperatingHours, HumanIdentifier, PatientLifecycle
from database.v1_1.sequences import mint_mrn, mint_invoice_number, mint_claim_number


def backfill_mrns(db) -> int:
    """Mint an MRN for every patient that doesn't already have one."""
    patients_without_mrn = (
        db.query(Patient)
        .outerjoin(
            HumanIdentifier,
            (HumanIdentifier.entity_type == "patient")
            & (HumanIdentifier.entity_id == Patient.id)
            & (HumanIdentifier.kind == "mrn"),
        )
        .filter(HumanIdentifier.id.is_(None))
        .all()
    )
    for p in patients_without_mrn:
        mint_mrn(db, p.clinic_id, p.id, p.last_name, year=(p.created_at.year if p.created_at else None))
    return len(patients_without_mrn)


def backfill_invoice_numbers(db) -> int:
    """Mint invoice_number for every invoice past 'draft'."""
    issued_invoices = (
        db.query(Invoice)
        .filter(Invoice.status.in_(("issued", "partial", "paid")))
        .outerjoin(
            HumanIdentifier,
            (HumanIdentifier.entity_type == "invoice")
            & (HumanIdentifier.entity_id == Invoice.id)
            & (HumanIdentifier.kind == "invoice_number"),
        )
        .filter(HumanIdentifier.id.is_(None))
        .all()
    )
    for inv in issued_invoices:
        year = (inv.issued_at or inv.created_at).year if (inv.issued_at or getattr(inv, "created_at", None)) else None
        mint_invoice_number(db, inv.clinic_id, inv.id, year=year)
    return len(issued_invoices)


def backfill_claim_numbers(db) -> int:
    """Mint claim_number for every claim past 'draft'."""
    submitted_claims = (
        db.query(InsuranceClaim)
        .filter(InsuranceClaim.status.in_(("submitted", "accepted", "adjudicated", "paid", "rejected", "partial")))
        .outerjoin(
            HumanIdentifier,
            (HumanIdentifier.entity_type == "claim")
            & (HumanIdentifier.entity_id == InsuranceClaim.id)
            & (HumanIdentifier.kind == "claim_number"),
        )
        .filter(HumanIdentifier.id.is_(None))
        .all()
    )
    for c in submitted_claims:
        year = (c.submitted_at or c.created_at).year if (c.submitted_at or getattr(c, "created_at", None)) else None
        mint_claim_number(db, c.clinic_id, c.id, year=year)
    return len(submitted_claims)


def backfill_operating_hours(db) -> int:
    """Seed Mon-Fri rows from each clinic's working_hour_start/end if no
    ClinicOperatingHours rows exist for that clinic."""
    clinics = db.query(Clinic).all()
    inserted = 0
    for c in clinics:
        existing = (
            db.query(ClinicOperatingHours)
            .filter_by(clinic_id=c.id)
            .first()
        )
        if existing:
            continue
        start = time(c.working_hour_start or 9, 0)
        end = time(c.working_hour_end or 17, 0)
        for dow in range(5):  # Mon-Fri
            db.add(ClinicOperatingHours(
                clinic_id=c.id,
                day_of_week=dow,
                open_at=start,
                close_at=end,
                is_closed=False,
            ))
            inserted += 1
    return inserted


def backfill_communication_preferences(db) -> int:
    """For every patient with a phone, ensure a default sms preference row
    exists (opted_in=true). Don't touch existing rows."""
    patients = db.query(Patient).filter(Patient.phone.isnot(None), Patient.phone != "").all()
    inserted = 0
    for p in patients:
        existing = (
            db.query(PatientCommunicationPreference)
            .filter_by(clinic_id=p.clinic_id, patient_id=p.id, channel="sms")
            .first()
        )
        if existing:
            continue
        db.add(PatientCommunicationPreference(
            clinic_id=p.clinic_id,
            patient_id=p.id,
            channel="sms",
            opted_in=True,
            language="en",
        ))
        inserted += 1
    return inserted


def backfill_patient_lifecycle(db) -> int:
    """Seed PatientLifecycle.status='active' for every existing patient that
    doesn't have a lifecycle row yet. Preserves prior behavior — every
    pre-existing patient was effectively active before this table existed."""
    patients_without_row = (
        db.query(Patient)
        .outerjoin(PatientLifecycle, PatientLifecycle.patient_id == Patient.id)
        .filter(PatientLifecycle.id.is_(None))
        .all()
    )
    now = datetime.utcnow()
    for p in patients_without_row:
        db.add(PatientLifecycle(
            clinic_id=p.clinic_id,
            patient_id=p.id,
            status="active",
            registered_at=p.created_at or now,
            last_status_change_at=now,
            notes="backfilled — pre-lifecycle patient",
        ))
    return len(patients_without_row)


def main() -> None:
    db = SessionLocal()
    try:
        print("Running v1.1 backfill...")
        mrn_count = backfill_mrns(db)
        inv_count = backfill_invoice_numbers(db)
        claim_count = backfill_claim_numbers(db)
        hours_count = backfill_operating_hours(db)
        prefs_count = backfill_communication_preferences(db)
        lifecycle_count = backfill_patient_lifecycle(db)
        db.commit()
        print(f"  MRNs minted:                    {mrn_count}")
        print(f"  Invoice numbers minted:         {inv_count}")
        print(f"  Claim numbers minted:           {claim_count}")
        print(f"  Operating hours rows seeded:    {hours_count}")
        print(f"  Communication preferences seeded: {prefs_count}")
        print(f"  Patient lifecycle rows seeded:  {lifecycle_count}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

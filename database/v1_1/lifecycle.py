"""
Patient lifecycle helpers.

A patient's `PatientLifecycle.status` answers "is this person fully
registered yet?" — distinct from `consent_approved`, `insurance_provider`,
etc., which are individual data points.

Default behavior when no row exists: treat as `active`. This preserves v1
semantics for any patient that existed before the lifecycle table was added.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import Patient
from database.clinical.models import PatientConsent, PatientInsurance
from database.v1_1.models import PatientLifecycle, PATIENT_STATUSES


def get_status(db: Session, patient_id: str) -> str:
    row = db.query(PatientLifecycle).filter_by(patient_id=patient_id).first()
    if row is None:
        return "active"
    return row.status


def set_status(
    db: Session,
    patient_id: str,
    clinic_id: str,
    status: str,
    notes: Optional[str] = None,
) -> PatientLifecycle:
    if status not in PATIENT_STATUSES:
        raise ValueError(f"invalid status {status!r}; expected one of {PATIENT_STATUSES}")
    row = db.query(PatientLifecycle).filter_by(patient_id=patient_id).first()
    now = datetime.utcnow()
    if row is None:
        row = PatientLifecycle(
            clinic_id=clinic_id,
            patient_id=patient_id,
            status=status,
            last_status_change_at=now,
            registered_at=(now if status == "active" else None),
            notes=notes,
        )
        db.add(row)
    else:
        if row.status != status:
            row.status = status
            row.last_status_change_at = now
            if status == "active" and row.registered_at is None:
                row.registered_at = now
        if notes is not None:
            row.notes = notes
    db.flush()
    return row


def is_complete_for_active(db: Session, patient: Patient) -> bool:
    """Returns True iff the patient has the minimum data set we expect for a
    fully-registered patient: first_name, last_name, phone, dob, consent
    on file, and at least one insurance row (or `is_minor` with guardian)."""
    if not (patient.first_name and patient.last_name and patient.phone):
        return False
    if patient.dob is None:
        return False
    if not patient.consent_approved:
        # Accept either the v1 boolean OR a row in patient_consent
        consent_row = (
            db.query(PatientConsent)
            .filter_by(clinic_id=patient.clinic_id, patient_id=patient.id)
            .first()
        )
        if consent_row is None:
            return False
    has_insurance = (
        db.query(PatientInsurance)
        .filter_by(clinic_id=patient.clinic_id, patient_id=patient.id)
        .first()
        is not None
    )
    if not has_insurance and not patient.is_minor:
        # Adults need at least an insurance record; minors are gated by guardian fields instead
        return False
    return True


def promote_if_complete(db: Session, patient: Patient) -> str:
    """Flip status from `pending` to `active` when the patient now has the
    required data. Returns the resulting status. No-op if already active or
    if data still incomplete."""
    current = get_status(db, patient.id)
    if current != "pending":
        return current
    if is_complete_for_active(db, patient):
        set_status(db, patient.id, patient.clinic_id, "active",
                   notes="auto-promoted: all required fields present")
        return "active"
    return "pending"

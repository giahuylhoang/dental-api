"""
Helpers for honoring `patient_communication_preferences` (v1.1).

Convention: absence of a row means "no preference set" → default opted-in.
Callers should treat `is_opted_in(...) == False` as "skip dispatch".

The default behavior preserves v1 semantics: existing notification call sites
that don't pass patient_id/clinic_id default to opted-in and continue working.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database.clinical.models import PatientCommunicationPreference


def is_opted_in(
    db: Session,
    clinic_id: Optional[str],
    patient_id: Optional[str],
    channel: str,
) -> bool:
    """Return True if dispatch on `channel` is allowed for this patient.

    Falls back to True when clinic_id or patient_id is None (no preference
    context available) — preserves v1 behavior for legacy callers.
    """
    if not clinic_id or not patient_id:
        return True
    pref = (
        db.query(PatientCommunicationPreference)
        .filter_by(clinic_id=clinic_id, patient_id=patient_id, channel=channel)
        .first()
    )
    if pref is None:
        return True
    if not pref.opted_in:
        return False
    dnc = pref.do_not_contact_until
    if dnc is not None:
        now = datetime.now(timezone.utc) if dnc.tzinfo else datetime.utcnow()
        if dnc > now:
            return False
    return True

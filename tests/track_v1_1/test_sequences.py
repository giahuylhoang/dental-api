"""Sequence allocator + human identifier tests (v1.1)."""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from database.models import Patient, Clinic, DEFAULT_CLINIC_ID
from database.v1_1.sequences import (
    mint_mrn,
    mint_invoice_number,
    mint_claim_number,
    lookup,
)


def _patient(db, last_name="Smith", clinic_id=DEFAULT_CLINIC_ID) -> Patient:
    p = Patient(id=str(uuid.uuid4()), clinic_id=clinic_id, first_name="P",
                last_name=last_name, phone="5550000000")
    db.add(p)
    db.flush()
    return p


def test_mrn_format_and_idempotency(db_session):
    p = _patient(db_session, last_name="Doe")
    mrn1 = mint_mrn(db_session, "default", p.id, "Doe", year=2026)
    mrn2 = mint_mrn(db_session, "default", p.id, "Doe", year=2026)
    assert mrn1 == mrn2  # idempotent
    assert mrn1.startswith("DOE-2026-")
    assert mrn1.split("-")[-1].isdigit() and len(mrn1.split("-")[-1]) == 4


def test_mrn_sequence_increments_per_clinic(db_session):
    p1 = _patient(db_session, last_name="A")
    p2 = _patient(db_session, last_name="B")
    m1 = mint_mrn(db_session, "default", p1.id, "A", year=2026)
    m2 = mint_mrn(db_session, "default", p2.id, "B", year=2026)
    seq1 = int(m1.split("-")[-1])
    seq2 = int(m2.split("-")[-1])
    assert seq2 == seq1 + 1


def test_mrn_per_clinic_isolation(db_session):
    other = Clinic(id="clinic-x", name="Clinic X")
    db_session.add(other); db_session.flush()
    p1 = _patient(db_session, last_name="One", clinic_id="default")
    p2 = _patient(db_session, last_name="Two", clinic_id="clinic-x")
    m1 = mint_mrn(db_session, "default", p1.id, "One", year=2026)
    m2 = mint_mrn(db_session, "clinic-x", p2.id, "Two", year=2026)
    # Both clinics start at sequence 0001 — clinic-scoped
    assert m1.endswith("-0001")
    assert m2.endswith("-0001")


def test_invoice_and_claim_number_format(db_session):
    p = _patient(db_session)
    inv_id = str(uuid.uuid4())
    claim_id = str(uuid.uuid4())
    inum = mint_invoice_number(db_session, "default", inv_id, year=2026)
    cnum = mint_claim_number(db_session, "default", claim_id, year=2026)
    assert inum == "INV-2026-000001"
    assert cnum == "CLM-2026-000001"


def test_lookup_returns_value(db_session):
    p = _patient(db_session, last_name="Lookup")
    minted = mint_mrn(db_session, "default", p.id, "Lookup", year=2026)
    assert lookup(db_session, "patient", p.id, "mrn") == minted
    assert lookup(db_session, "patient", "does-not-exist", "mrn") is None


def test_human_identifier_value_uniqueness_per_clinic(db_session):
    """Two patients in the same clinic cannot share an MRN value."""
    from database.v1_1.models import HumanIdentifier
    db_session.add(HumanIdentifier(
        clinic_id="default", entity_type="patient", entity_id="abc",
        kind="mrn", value="DUP-2026-0001",
    ))
    db_session.commit()
    db_session.add(HumanIdentifier(
        clinic_id="default", entity_type="patient", entity_id="def",
        kind="mrn", value="DUP-2026-0001",
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

"""Communication preferences gate (v1.1)."""
import uuid
from datetime import datetime, timedelta

import pytest

from database.models import Patient
from database.clinical.models import PatientCommunicationPreference
from database.clinical.communication_prefs import is_opted_in


def _patient(db, clinic_id="default") -> Patient:
    p = Patient(id=str(uuid.uuid4()), clinic_id=clinic_id, first_name="P", last_name="T",
                phone="5551234567")
    db.add(p)
    db.flush()
    return p


def test_default_opted_in_when_no_row(db_session):
    p = _patient(db_session)
    assert is_opted_in(db_session, "default", p.id, "sms") is True
    assert is_opted_in(db_session, "default", p.id, "email") is True


def test_explicit_opt_out_blocks(db_session):
    p = _patient(db_session)
    db_session.add(PatientCommunicationPreference(
        clinic_id="default", patient_id=p.id, channel="sms", opted_in=False, language="en",
    ))
    db_session.commit()
    assert is_opted_in(db_session, "default", p.id, "sms") is False
    # Other channels still default opted-in
    assert is_opted_in(db_session, "default", p.id, "email") is True


def test_do_not_contact_until_in_future_blocks(db_session):
    p = _patient(db_session)
    future = datetime.utcnow() + timedelta(days=30)
    db_session.add(PatientCommunicationPreference(
        clinic_id="default", patient_id=p.id, channel="sms", opted_in=True,
        do_not_contact_until=future, language="en",
    ))
    db_session.commit()
    assert is_opted_in(db_session, "default", p.id, "sms") is False


def test_do_not_contact_until_in_past_does_not_block(db_session):
    p = _patient(db_session)
    past = datetime.utcnow() - timedelta(days=1)
    db_session.add(PatientCommunicationPreference(
        clinic_id="default", patient_id=p.id, channel="sms", opted_in=True,
        do_not_contact_until=past, language="en",
    ))
    db_session.commit()
    assert is_opted_in(db_session, "default", p.id, "sms") is True


def test_unique_clinic_patient_channel(db_session):
    from sqlalchemy.exc import IntegrityError
    p = _patient(db_session)
    db_session.add(PatientCommunicationPreference(
        clinic_id="default", patient_id=p.id, channel="sms", opted_in=True, language="en",
    ))
    db_session.commit()
    db_session.add(PatientCommunicationPreference(
        clinic_id="default", patient_id=p.id, channel="sms", opted_in=False, language="en",
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

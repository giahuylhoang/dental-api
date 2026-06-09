"""Tests for Clinic.sms_from_number column (per-clinic Telnyx SMS sender)."""

from database.models import Clinic


def test_clinic_sms_from_number_round_trip(db_session):
    c = db_session.query(Clinic).first()
    if c is None:
        c = Clinic(id="test-c", name="Test", timezone="America/Edmonton")
        db_session.add(c)
        db_session.commit()
    c.sms_from_number = "+14035550000"
    db_session.commit()
    db_session.refresh(c)
    assert c.sms_from_number == "+14035550000"


def test_clinic_sms_from_number_defaults_to_none(db_session):
    c = Clinic(id="newly-created-clinic", name="New", timezone="America/Edmonton")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    assert c.sms_from_number is None

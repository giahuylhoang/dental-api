"""Referral + ReferralDocument ORM models create and relate correctly."""
from datetime import date

from database.models import Clinic, Referral, ReferralDocument, ReferralStatus


def _clinic(db, cid="mm-test"):
    c = Clinic(id=cid, name="Market Mall Test")
    db.add(c)
    db.flush()
    return c


def test_referral_defaults_and_documents(db_session):
    db = db_session
    _clinic(db)
    ref = Referral(
        clinic_id="mm-test",
        patient_name="Albert Nasser",
        patient_phone="825-747-5308",
        referred_by="Cedarbrae Family Dental",
        tx_plan="Consultation please!",
        proposed_extraction_date=date(2026, 7, 1),
        provider_id=None,  # Either
    )
    db.add(ref)
    db.flush()

    assert ref.id  # uuid assigned
    assert ref.status == ReferralStatus.NEW
    assert ref.source == "public-referral"

    doc = ReferralDocument(
        clinic_id="mm-test",
        referral_id=ref.id,
        kind="xray",
        storage_url="mm-test/referrals/" + ref.id + "/abc.jpg",
        storage_backend="local",
        mime="image/jpeg",
        size_bytes=12345,
        original_name="panoramic.jpg",
    )
    db.add(doc)
    db.flush()

    db.refresh(ref)
    assert len(ref.documents) == 1
    assert ref.documents[0].original_name == "panoramic.jpg"


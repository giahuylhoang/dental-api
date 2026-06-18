from database.models import Clinic, Patient
from services.holds import upsert_patient_by_phone


def _clinic(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton"))
    db.commit()


def test_creates_patient_when_phone_unknown(db_session):
    _clinic(db_session)
    p = upsert_patient_by_phone(db_session, clinic_id="mm", name="Jane Doe",
                                phone="4035551234", email="j@x.com")
    db_session.commit()
    assert p.id is not None
    assert p.first_name == "Jane" and p.last_name == "Doe"
    assert p.phone == "4035551234"


def test_reuses_existing_patient_same_phone(db_session):
    _clinic(db_session)
    db_session.add(Patient(id="pat-1", first_name="Jane", last_name="Doe",
                           clinic_id="mm", phone="4035551234"))
    db_session.commit()
    p = upsert_patient_by_phone(db_session, clinic_id="mm", name="Janey",
                                phone="4035551234", email=None)
    assert p.id == "pat-1"


def test_phone_match_is_scoped_to_clinic(db_session):
    db_session.add_all([
        Clinic(id="mm", name="MM", timezone="America/Edmonton"),
        Clinic(id="other", name="Other", timezone="America/Edmonton"),
        Patient(id="pat-other", first_name="X", last_name="Y",
                clinic_id="other", phone="4035551234"),
    ])
    db_session.commit()
    p = upsert_patient_by_phone(db_session, clinic_id="mm", name="Jane Doe",
                                phone="4035551234", email=None)
    db_session.commit()
    assert p.clinic_id == "mm" and p.id != "pat-other"

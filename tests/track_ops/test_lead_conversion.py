"""Test lead-to-patient conversion: idempotent, source preserved."""
import pytest
from database.models import Lead, LeadStatus, Patient, DEFAULT_CLINIC_ID
from database.ops.models import LeadEvent


def _make_lead(db, name="John Doe", source="facebook"):
    lead = Lead(
        clinic_id=DEFAULT_CLINIC_ID,
        name=name,
        phone="5551234",
        email="john@example.com",
        source=source,
        status=LeadStatus.NEW,
    )
    db.add(lead)
    db.flush()
    return lead


def test_lead_conversion_creates_patient(client, db_session):
    """First call creates patient and marks lead CONVERTED."""
    lead = _make_lead(db_session)
    db_session.commit()

    r = client.post(f"/api/v2/crm/leads/{lead.id}/convert", json={"create_patient": True})
    assert r.status_code == 200
    data = r.json()
    assert data["patient_id"] is not None
    assert data["created"] is True

    # Lead status updated
    db_session.refresh(lead)
    assert lead.status == LeadStatus.CONVERTED

    # Patient exists
    patient = db_session.query(Patient).filter(Patient.id == data["patient_id"]).first()
    assert patient is not None
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    assert patient.phone == lead.phone
    assert patient.email == lead.email


def test_lead_conversion_idempotent(client, db_session):
    """Second call returns same patient (idempotent)."""
    lead = _make_lead(db_session)
    db_session.commit()

    r1 = client.post(f"/api/v2/crm/leads/{lead.id}/convert", json={"create_patient": True})
    patient_id_1 = r1.json()["patient_id"]

    r2 = client.post(f"/api/v2/crm/leads/{lead.id}/convert", json={"create_patient": True})
    assert r2.status_code == 200
    assert r2.json()["patient_id"] == patient_id_1
    assert r2.json()["created"] is False


def test_lead_conversion_source_preserved(client, db_session):
    """Source is preserved in lead event payload."""
    lead = _make_lead(db_session, source="google_ads")
    db_session.commit()

    client.post(f"/api/v2/crm/leads/{lead.id}/convert", json={"create_patient": True})

    event = db_session.query(LeadEvent).filter(
        LeadEvent.lead_id == lead.id,
        LeadEvent.kind == "converted",
    ).first()
    assert event is not None
    assert event.payload["source"] == "google_ads"


def test_lead_conversion_no_patient(client, db_session):
    """create_patient=False → no patient created, lead still converted."""
    lead = _make_lead(db_session)
    db_session.commit()

    r = client.post(f"/api/v2/crm/leads/{lead.id}/convert", json={"create_patient": False})
    assert r.status_code == 200
    assert r.json()["patient_id"] is None

    db_session.refresh(lead)
    assert lead.status == LeadStatus.CONVERTED

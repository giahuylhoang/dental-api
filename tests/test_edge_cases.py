"""Edge case tests for robustness."""
import pytest
import uuid


def test_edge_empty_clinic(client, db_session):
    """Empty clinic renders without errors."""
    from database.models import Clinic
    clinic_id = f"empty-{uuid.uuid4().hex[:8]}"
    clinic = Clinic(id=clinic_id, name="Empty Clinic", display_name="Empty Clinic", timezone="America/Edmonton")
    db_session.add(clinic)
    db_session.commit()
    
    # Test various endpoints with empty clinic
    resp = client.get("/api/appointments", headers={"X-Clinic-Id": clinic_id})
    assert resp.status_code == 200
    assert resp.json() == []
    
    resp = client.get("/api/patients", headers={"X-Clinic-Id": clinic_id})
    assert resp.status_code == 200
    assert resp.json() == []
    
    resp = client.get("/api/v2/reporting/kpi", headers={"X-Clinic-Id": clinic_id})
    assert resp.status_code == 200


def test_edge_adversarial_unicode(client, db_session):
    """Unicode, long strings, SQL-quote chars round-trip cleanly."""
    from database.models import Clinic, Patient
    clinic_id = f"adv-{uuid.uuid4().hex[:8]}"
    clinic = Clinic(id=clinic_id, name="Adversarial Clinic", display_name="Adversarial Clinic", timezone="America/Edmonton")
    db_session.add(clinic)
    db_session.flush()
    
    # Unicode names
    patients_data = [
        ("José", "García"),
        ("田中", "太郎"),
        ("Müller", "Hans"),
        ("O'Brien", "Patrick"),
        ("Test", "User'; DROP TABLE patients; --"),
        ("Emoji", "Test 🦷💉"),
    ]
    
    for i, (first, last) in enumerate(patients_data):
        patient = Patient(
            id=f"P-ADV-{clinic_id}-{i:04d}",
            clinic_id=clinic_id,
            first_name=first,
            last_name=last,
            phone=f"555-{i:04d}",
        )
        db_session.add(patient)
    db_session.commit()
    
    # Verify patients were created
    resp = client.get("/api/patients", headers={"X-Clinic-Id": clinic_id})
    assert resp.status_code == 200
    patients = resp.json()
    assert len(patients) >= 6
    
    # Check unicode names round-trip
    names = [p.get("first_name", "") for p in patients]
    assert "José" in names
    assert "田中" in names


def test_edge_empty_kpi(client, db_session):
    """KPI endpoint handles empty data gracefully."""
    from database.models import Clinic
    clinic_id = f"empty-kpi-{uuid.uuid4().hex[:8]}"
    clinic = Clinic(id=clinic_id, name="Empty KPI Clinic", display_name="Empty KPI Clinic", timezone="America/Edmonton")
    db_session.add(clinic)
    db_session.commit()
    
    resp = client.get("/api/v2/reporting/kpi", headers={"X-Clinic-Id": clinic_id})
    assert resp.status_code == 200
    data = resp.json()
    
    # Should return valid structure with zero values
    assert data["production_this_month"] == 0
    assert data["no_show_rate"] == 0

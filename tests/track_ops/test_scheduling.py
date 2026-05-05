"""Tests for scheduling v2 reschedule endpoint Pydantic validation."""
import pytest
from datetime import datetime, timedelta


class TestRescheduleValidation:
    """Reschedule endpoint should validate body with Pydantic."""

    @pytest.fixture
    def appointment_id(self, client, db_session):
        """Create an appointment to reschedule."""
        from database.models import Patient, Provider, Appointment, AppointmentStatus
        
        p = Patient(id="sched-test-patient", first_name="Test", last_name="Patient", clinic_id="default")
        db_session.add(p)
        
        prov = db_session.query(Provider).filter(Provider.clinic_id == "default").first()
        if not prov:
            prov = Provider(id=999, name="Test Provider", clinic_id="default")
            db_session.add(prov)
        
        db_session.flush()
        
        start = datetime.now() + timedelta(days=1)
        apt = Appointment(
            id="sched-test-apt",
            clinic_id="default",
            patient_id=p.id,
            provider_id=prov.id,
            start_time=start,
            end_time=start + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
        )
        db_session.add(apt)
        db_session.commit()
        return apt.id

    def test_reschedule_empty_body_returns_422(self, client, appointment_id):
        """Empty body should return 422."""
        resp = client.post(f"/api/v2/scheduling/appointments/{appointment_id}/reschedule", json={})
        assert resp.status_code == 422

    def test_reschedule_missing_end_time_returns_422(self, client, appointment_id):
        """Missing end_time should return 422."""
        resp = client.post(
            f"/api/v2/scheduling/appointments/{appointment_id}/reschedule",
            json={"start_time": "2026-05-10T10:00:00"}
        )
        assert resp.status_code == 422

    def test_reschedule_missing_start_time_returns_422(self, client, appointment_id):
        """Missing start_time should return 422."""
        resp = client.post(
            f"/api/v2/scheduling/appointments/{appointment_id}/reschedule",
            json={"end_time": "2026-05-10T11:00:00"}
        )
        assert resp.status_code == 422

    def test_reschedule_valid_body_returns_200(self, client, appointment_id):
        """Valid body should return 200."""
        resp = client.post(
            f"/api/v2/scheduling/appointments/{appointment_id}/reschedule",
            json={
                "start_time": "2026-05-10T10:00:00",
                "end_time": "2026-05-10T11:00:00"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "appointment_id" in data

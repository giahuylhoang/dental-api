"""Tests for /api/portal/clinics/{cid}/dashboard (SQL aggregations)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import app
from database.models import CallLog, Patient

client = TestClient(app)


def test_dashboard_empty_returns_zeros(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["calls_total"] == 0
    assert body["calls_booked"] == 0
    assert body["patients_total"] == 0


def test_dashboard_counts(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default"])
    db_session.add(CallLog(id="c1", clinic_id="default", started_at=datetime.now(timezone.utc), outcome="booked"))
    db_session.add(CallLog(id="c2", clinic_id="default", started_at=datetime.now(timezone.utc), outcome="hangup"))
    db_session.add(Patient(id="p1", clinic_id="default", first_name="X", phone="+14030000000"))
    db_session.commit()

    r = client.get("/api/portal/clinics/default/dashboard")
    body = r.json()
    assert body["calls_total"] == 2
    assert body["calls_booked"] == 1
    assert body["patients_total"] == 1


def test_dashboard_scoped_per_clinic(db_session, override_portal_user):
    override_portal_user(clinic_ids=["default", "other_clinic"])
    # Insert into 'default' (already exists) and into 'other_clinic' (must create first)
    from database.models import Clinic
    db_session.add(Clinic(id="other_clinic", name="Other"))
    db_session.flush()
    db_session.add(CallLog(id="c_def", clinic_id="default", started_at=datetime.now(timezone.utc)))
    db_session.add(CallLog(id="c_oth", clinic_id="other_clinic", started_at=datetime.now(timezone.utc)))
    db_session.commit()

    r1 = client.get("/api/portal/clinics/default/dashboard")
    assert r1.json()["calls_total"] == 1
    r2 = client.get("/api/portal/clinics/other_clinic/dashboard")
    assert r2.json()["calls_total"] == 1

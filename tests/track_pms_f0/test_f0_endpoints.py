"""PMS Module F0 — backend schema fill + demo clinic seed tests."""
import re
import os
import pytest

CLINIC_HEADERS = {"X-Clinic-Id": "default"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_patient(client):
    r = client.post("/api/patients", json={
        "first_name": "Test", "last_name": "Patient",
        "phone": "5550001111", "email": "test.f0@example.com",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _seed_denture_case_and_vendor(client):
    """Seed a denture case and vendor directly via DB."""
    from database.clinical.models import DentureCase, LabVendor
    from database.connection import get_db
    from api.main import app
    db = next(app.dependency_overrides[get_db]())
    patient_id = _create_patient(client)
    dc = DentureCase(
        clinic_id="default", patient_id=patient_id,
        arch="upper", case_type="complete", current_stage="consult", status="open",
    )
    db.add(dc)
    db.flush()
    vendor = LabVendor(
        clinic_id="default", name="Test Lab", contact_email="lab@test.com",
        sla_days=7, is_active=True,
    )
    db.add(vendor)
    db.flush()
    db.commit()
    return dc.id, vendor.id, patient_id


def _create_treatment_plan(client, patient_id):
    r = client.post("/api/v2/treatment-plans", json={
        "patient_id": patient_id,
        "items": [{"procedure_code": "01234", "description": "Test", "fee": 100.0}],
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


# ---------------------------------------------------------------------------
# 1. lab_case_number auto-generated
# ---------------------------------------------------------------------------

def test_lab_case_number_auto_generated(client):
    dc_id, vendor_id, _ = _seed_denture_case_and_vendor(client)
    r = client.post("/api/v2/lab/cases", json={
        "denture_case_id": dc_id,
        "vendor_id": vendor_id,
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert "case_number" in body
    assert re.match(r"LC-\d{4}-\d{4}", body["case_number"]), f"Bad case_number: {body['case_number']}"


# ---------------------------------------------------------------------------
# 2. lab_case links to treatment_plan
# ---------------------------------------------------------------------------

def test_lab_case_links_to_treatment_plan(client):
    dc_id, vendor_id, patient_id = _seed_denture_case_and_vendor(client)
    plan_id = _create_treatment_plan(client, patient_id)

    r = client.post("/api/v2/lab/cases", json={
        "denture_case_id": dc_id,
        "vendor_id": vendor_id,
        "treatment_plan_id": plan_id,
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body.get("treatment_plan_id") == plan_id


# ---------------------------------------------------------------------------
# 3. communication thread_key computed on send
# ---------------------------------------------------------------------------

def test_communication_thread_key_computed(client):
    patient_id = _create_patient(client)
    r = client.post("/api/v2/communications/send", json={
        "patient_id": patient_id,
        "channel": "sms",
        "body": "Hello from F0 test",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body.get("thread_key") == f"{patient_id}:sms"


# ---------------------------------------------------------------------------
# 4. communication read_at is null by default
# ---------------------------------------------------------------------------

def test_communication_read_at_nullable_default_null(client):
    patient_id = _create_patient(client)
    r = client.post("/api/v2/communications/send", json={
        "patient_id": patient_id,
        "channel": "email",
        "body": "Test read_at null",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert "read_at" in body
    assert body["read_at"] is None


# ---------------------------------------------------------------------------
# 5. thread mark-read endpoint
# ---------------------------------------------------------------------------

def test_thread_mark_read_endpoint(client):
    patient_id = _create_patient(client)
    channel = "sms"
    thread_key = f"{patient_id}:{channel}"

    # Send 3 messages on the same thread
    for i in range(3):
        r = client.post("/api/v2/communications/send", json={
            "patient_id": patient_id,
            "channel": channel,
            "body": f"Message {i}",
        }, headers=CLINIC_HEADERS)
        assert r.status_code in (200, 201), r.text

    # Mark thread as read
    r = client.patch(f"/api/v2/communications/threads/{thread_key}/read",
                     headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("updated") == 3

    # Verify all messages now have read_at set
    r2 = client.get(f"/api/v2/communications?patient_id={patient_id}&channel={channel}",
                    headers=CLINIC_HEADERS)
    assert r2.status_code == 200, r2.text
    msgs = r2.json()
    assert all(m["read_at"] is not None for m in msgs), "Some messages still unread"


# ---------------------------------------------------------------------------
# 6. settings GET returns clinic config
# ---------------------------------------------------------------------------

def test_settings_get_returns_clinic_config(client):
    r = client.get("/api/v2/settings/clinic", headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "timezone" in body
    assert "working_hour_start" in body
    assert "working_hour_end" in body


# ---------------------------------------------------------------------------
# 7. settings PUT updates clinic config
# ---------------------------------------------------------------------------

def test_settings_put_updates_clinic_config(client):
    r = client.put("/api/v2/settings/clinic", json={"display_name": "Smile Co"},
                   headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text

    r2 = client.get("/api/v2/settings/clinic", headers=CLINIC_HEADERS)
    assert r2.status_code == 200, r2.text
    assert r2.json()["display_name"] == "Smile Co"


# ---------------------------------------------------------------------------
# 8. settings integrations returns provider health
# ---------------------------------------------------------------------------

def test_settings_integrations_returns_provider_health(client, monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest123")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("TWILIO_WHATSAPP_FROM", raising=False)

    r = client.get("/api/v2/settings/integrations", headers=CLINIC_HEADERS)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sms"]["enabled"] is True
    assert body["email"]["enabled"] is False
    assert body["whatsapp"]["enabled"] is False


# ---------------------------------------------------------------------------
# 9. seed_demo_clinic idempotent
# ---------------------------------------------------------------------------

def test_seed_demo_clinic_idempotent():
    """Call seed twice; second call should be a no-op."""
    import io
    from contextlib import redirect_stdout
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import database.models  # noqa
    import database.clinical.models  # noqa
    import database.ops.models  # noqa
    from database.connection import Base

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _sqlite_skip = {"rag_docs"}
    _sqlite_tables = [t for t in Base.metadata.sorted_tables if t.name not in _sqlite_skip]
    Base.metadata.create_all(bind=test_engine, tables=_sqlite_tables)

    # Patch the engine used by seed_demo_clinic
    import database.connection as _conn
    original_engine = _conn.engine
    _conn.engine = test_engine
    try:
        from scripts.seed_demo_clinic import main as seed_main

        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            seed_main()
        out1 = buf1.getvalue()
        assert "already seeded" not in out1

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            seed_main()
        out2 = buf2.getvalue()
        assert "already seeded" in out2
    finally:
        _conn.engine = original_engine


# ---------------------------------------------------------------------------
# 10. alembic round-trip
# ---------------------------------------------------------------------------

def test_alembic_round_trip(tmp_path):
    """upgrade head → downgrade -1 → upgrade head — no errors."""
    import subprocess
    import sys

    # project root is 2 levels up from this file
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = tmp_path / "alembic_test.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}

    def run(cmd):
        result = subprocess.run(
            [sys.executable, "-m", "alembic"] + cmd,
            capture_output=True, text=True, env=env,
            cwd=project_root,
        )
        assert result.returncode == 0, f"alembic {cmd} failed:\n{result.stdout}\n{result.stderr}"

    run(["upgrade", "head"])
    run(["downgrade", "-1"])
    run(["upgrade", "head"])

"""Tests: audit log — create/update/delete Patient produces audit rows."""
import pytest
import bcrypt as _bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID, Patient
from database.auth.models import User, Role, UserRole, AuditLog
from database.auth.audit import set_audit_context
from api.main import app


def _hash(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()


@pytest.fixture()
def setup(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    session.add(Clinic(id=DEFAULT_CLINIC_ID, name="TC", timezone="UTC", working_hour_start=9, working_hour_end=17))
    session.flush()
    role = Role(name="admin", clinic_id=None, permissions=["*.*"])
    session.add(role)
    session.flush()
    user = User(
        clinic_id=DEFAULT_CLINIC_ID,
        email="admin@t.com",
        password_hash=_hash("pw"),
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()

    def override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        resp = c.post("/api/v2/auth/login", json={"email": "admin@t.com", "password": "pw"})
        token = resp.json()["access_token"]
        yield c, session, user, token
    app.dependency_overrides.clear()
    session.close()


def test_audit_on_patient_create(setup):
    c, session, user, token = setup
    set_audit_context(user.id, "127.0.0.1", "test-agent")

    patient = Patient(
        clinic_id=DEFAULT_CLINIC_ID,
        first_name="John",
        last_name="Doe",
    )
    session.add(patient)
    session.commit()

    logs = session.query(AuditLog).filter(AuditLog.entity_type == "patients").all()
    assert len(logs) >= 1
    log = logs[-1]
    assert log.action == "insert"
    assert log.user_id == user.id
    assert log.after is not None
    assert log.after.get("first_name") == "John"


def test_audit_on_patient_update(setup):
    c, session, user, token = setup
    set_audit_context(user.id, "127.0.0.1", "test-agent")

    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Jane", last_name="Smith")
    session.add(patient)
    session.commit()

    patient.first_name = "Janet"
    session.commit()

    logs = session.query(AuditLog).filter(
        AuditLog.entity_type == "patients", AuditLog.action == "update"
    ).all()
    assert len(logs) >= 1
    log = logs[-1]
    assert log.before is not None
    assert log.after is not None
    assert log.before.get("first_name") == "Jane"
    assert log.after.get("first_name") == "Janet"


def test_audit_on_patient_delete(setup):
    c, session, user, token = setup
    set_audit_context(user.id, "127.0.0.1", "test-agent")

    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Del", last_name="Me")
    session.add(patient)
    session.commit()

    session.delete(patient)
    session.commit()

    logs = session.query(AuditLog).filter(
        AuditLog.entity_type == "patients", AuditLog.action == "delete"
    ).all()
    assert len(logs) >= 1
    log = logs[-1]
    assert log.before is not None
    assert log.before.get("first_name") == "Del"
    assert log.after is None


def test_audit_log_has_user_id_and_ip(setup):
    c, session, user, token = setup
    set_audit_context(user.id, "10.0.0.1", "Mozilla/5.0")

    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="IP", last_name="Test")
    session.add(patient)
    session.commit()

    log = session.query(AuditLog).filter(
        AuditLog.entity_type == "patients", AuditLog.action == "insert"
    ).order_by(AuditLog.created_at.desc()).first()
    assert log.user_id == user.id
    assert log.ip == "10.0.0.1"
    assert log.user_agent == "Mozilla/5.0"

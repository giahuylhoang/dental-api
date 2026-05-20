"""Read-access audit hook (v1.1, PIPEDA)."""
import os

from database.auth.audit import (
    audit_reads_enabled,
    record_read,
    record_export,
    set_audit_context,
)
from database.auth.models import AuditLog


def test_audit_reads_disabled_by_default(monkeypatch, db_session):
    monkeypatch.delenv("AUDIT_READS", raising=False)
    assert audit_reads_enabled() is False
    record_read(db_session, "Patient", "abc", "default")
    db_session.commit()
    assert db_session.query(AuditLog).filter_by(action="read").count() == 0


def test_audit_reads_enabled_writes_row(monkeypatch, db_session):
    monkeypatch.setenv("AUDIT_READS", "true")
    set_audit_context("user-x", "127.0.0.1", "test-ua")
    record_read(db_session, "Patient", "patient-123", "default")
    db_session.commit()
    rows = db_session.query(AuditLog).filter_by(action="read").all()
    assert len(rows) == 1
    r = rows[0]
    assert r.entity_type == "Patient"
    assert r.entity_id == "patient-123"
    assert r.user_id == "user-x"
    assert r.ip == "127.0.0.1"
    assert r.user_agent == "test-ua"


def test_export_action(monkeypatch, db_session):
    monkeypatch.setenv("AUDIT_READS", "true")
    set_audit_context("user-y", "10.0.0.1", "csv-export")
    record_export(db_session, "PatientList", None, "default")
    db_session.commit()
    rows = db_session.query(AuditLog).filter_by(action="export").all()
    assert len(rows) == 1
    assert rows[0].entity_type == "PatientList"

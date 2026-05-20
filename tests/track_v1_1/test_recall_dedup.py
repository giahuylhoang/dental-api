"""Track 3 added Recall + RecallRule. v1.1 enforces at most one active recall
per (patient, rule) via a partial unique index."""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from database.models import Patient
from database.ops.models import RecallRule, Recall


def _seed_patient(db, clinic_id="default") -> Patient:
    p = Patient(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        first_name="Recall",
        last_name="Tester",
        phone=f"555000{int.from_bytes(uuid.uuid4().bytes[:2], 'big')}",
    )
    db.add(p)
    db.flush()
    return p


def test_active_recall_uniqueness(db_session):
    rule = RecallRule(clinic_id="default", name="6mo cleaning", trigger_event="annual",
                      offset_days=180, channel="sms")
    db_session.add(rule)
    db_session.flush()
    p = _seed_patient(db_session)

    db_session.add(Recall(clinic_id="default", patient_id=p.id, rule_id=rule.id,
                          due_at=datetime.utcnow() + timedelta(days=10), status="pending"))
    db_session.commit()

    # Second active recall for same (patient, rule) must fail
    db_session.add(Recall(clinic_id="default", patient_id=p.id, rule_id=rule.id,
                          due_at=datetime.utcnow() + timedelta(days=20), status="pending"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_completed_recall_does_not_block_new(db_session):
    rule = RecallRule(clinic_id="default", name="annual reline", trigger_event="reline",
                      offset_days=365, channel="email")
    db_session.add(rule)
    db_session.flush()
    p = _seed_patient(db_session)

    # First recall completed
    db_session.add(Recall(clinic_id="default", patient_id=p.id, rule_id=rule.id,
                          due_at=datetime.utcnow() - timedelta(days=1), status="completed"))
    db_session.commit()

    # New active recall on the same rule is allowed
    db_session.add(Recall(clinic_id="default", patient_id=p.id, rule_id=rule.id,
                          due_at=datetime.utcnow() + timedelta(days=365), status="pending"))
    db_session.commit()  # should not raise

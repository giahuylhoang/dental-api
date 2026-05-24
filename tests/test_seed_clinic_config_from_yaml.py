"""Seeder turns a YAML tree into rows; idempotent on second run."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.postgres


@pytest.fixture
def yaml_tree(tmp_path: Path) -> Path:
    """Build a minimal denturist clinic YAML tree at tmp_path/clinics/."""
    root = tmp_path / "clinics"
    (root / "base").mkdir(parents=True)
    (root / "market-mall-denture").mkdir(parents=True)

    (root / "base" / "denturist.yaml").write_text(yaml.safe_dump({
        "clinic": {
            "practice_type": "denturist",
            "assistant_name": "Emma",
            "ai_disclosure_required": True,
            "ai_disclosure_phrase": "I'm a virtual receptionist",
            "greeting_message": "base greeting",
            "pricing_preface": "preface",
            "pricing_dentures_range": "1700-2200",
            "treatment_steps_guardrail": "guardrail",
            "triage_questions": ["q1", "q2"],
            "feature_flags": {"sms_notifications": True, "ai_disclosure_v2": False},
        },
        "general_consultation_service_id": 700,
        "routing": {
            "timezone": "America/Edmonton",
            "ring_timeout_seconds": 20,
            "ai_after_hours": True,
            "ai_in_hours_overflow": True,
        },
    }))

    (root / "market-mall-denture" / "product.yaml").write_text(yaml.safe_dump({
        "extends": "../base/denturist.yaml",
        "clinic": {
            "name": "Market Mall Denture Clinic",
            "address": "123 Main, Calgary",
            "front_desk_phone": "+15879999999",
            "feature_flags": {"ai_disclosure_v2": True},
        },
        "general_consultation_service_id": 700,
        "knowledge_base_path": "knowledge/clinics/market-mall-denture",
    }))

    (root / "market-mall-denture" / "ops.yaml").write_text(yaml.safe_dump({
        "routing": {
            "timezone": "America/Edmonton",
            "dids": ["+15874023579"],
            "front_desk_numbers": [],
            "ring_timeout_seconds": 20,
            "hours": {"mon": {"open": "00:00", "close": "23:59"}},
            "holidays": ["2026-12-25"],
            "ai_after_hours": True,
            "ai_in_hours_overflow": True,
            "backup_number": "+13682990959",
            "ai_sip_uri": "sip:test@livekit",
        },
    }))
    return root


def test_seeder_creates_rows_first_run(pg_db_session, yaml_tree):
    from scripts.seed_clinic_config_from_yaml import seed_from_yaml
    # Pre-create the clinic shell so the FK exists (clinics.id is PK referenced by clinic_routing).
    from database.models import Clinic
    pg_db_session.add(Clinic(id="market-mall-denture", name="placeholder"))
    pg_db_session.flush()

    seed_from_yaml(pg_db_session, yaml_dir=yaml_tree)
    pg_db_session.flush()

    from database.models import PracticeType, ClinicRouting, ClinicClosure
    pt = pg_db_session.query(PracticeType).filter_by(id="denturist").one()
    assert pt.assistant_name == "Emma"
    assert pt.triage_questions == ["q1", "q2"]

    cr = pg_db_session.query(ClinicRouting).filter_by(clinic_id="market-mall-denture").one()
    assert cr.dids == ["+15874023579"]
    assert cr.ai_sip_uri == "sip:test@livekit"

    clinic = pg_db_session.query(Clinic).filter_by(id="market-mall-denture").one()
    assert clinic.practice_type_id == "denturist"
    assert clinic.feature_flags_overrides == {"ai_disclosure_v2": True}
    assert clinic.knowledge_base_path == "knowledge/clinics/market-mall-denture"

    holidays = pg_db_session.query(ClinicClosure).filter_by(
        clinic_id="market-mall-denture", kind="holiday",
    ).all()
    assert len(holidays) == 1


def test_seeder_is_idempotent(pg_db_session, yaml_tree):
    from scripts.seed_clinic_config_from_yaml import seed_from_yaml
    from database.models import Clinic, PracticeType, ClinicRouting
    pg_db_session.add(Clinic(id="market-mall-denture", name="placeholder"))
    pg_db_session.flush()

    seed_from_yaml(pg_db_session, yaml_dir=yaml_tree)
    pg_db_session.flush()
    seed_from_yaml(pg_db_session, yaml_dir=yaml_tree)
    pg_db_session.flush()

    assert pg_db_session.query(PracticeType).count() == 1
    assert pg_db_session.query(ClinicRouting).count() == 1


def test_seeder_skips_ai_voice_when_no_override(pg_db_session, yaml_tree):
    """Without product.yaml override, clinic_ai_voice row must NOT be created."""
    from scripts.seed_clinic_config_from_yaml import seed_from_yaml
    from database.models import Clinic, ClinicAiVoice
    pg_db_session.add(Clinic(id="market-mall-denture", name="placeholder"))
    pg_db_session.flush()
    seed_from_yaml(pg_db_session, yaml_dir=yaml_tree)
    pg_db_session.flush()

    voice = pg_db_session.query(ClinicAiVoice).filter_by(clinic_id="market-mall-denture").one_or_none()
    assert voice is None

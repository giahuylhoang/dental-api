"""Contract tests for GET /api/clinics/{clinic_id}/config."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.postgres


@pytest.fixture
def seeded_for_endpoint(pg_db_session):
    from database.models import (
        Clinic, ClinicRouting, PracticeType, Provider, ClinicClosure,
    )
    pg_db_session.add(PracticeType(
        id='denturist',
        assistant_name='Emma',
        ai_disclosure_required=True,
        ai_disclosure_phrase="I'm a virtual receptionist",
        greeting_message='hello',
        pricing_preface='preface',
        pricing_dentures_range='1700-2200',
        treatment_steps_guardrail='guardrail',
        triage_questions=['q1'],
        default_feature_flags={},
    ))
    pg_db_session.flush()  # avoid SA UoW issue seen in Task 3
    pg_db_session.add(Clinic(
        id='market-mall-denture', name='Market Mall',
        timezone='America/Edmonton', address='Calgary', contact_phone='+1',
        practice_type_id='denturist',
        knowledge_base_path='kb/mm', feature_flags_overrides={},
    ))
    pg_db_session.flush()
    pg_db_session.add(ClinicRouting(
        clinic_id='market-mall-denture',
        ring_timeout_seconds=20,
        ai_after_hours=True, ai_in_hours_overflow=True,
        backup_number='+15870000000', ai_sip_uri='sip:test',
        dids=['+15874023579'], front_desk_numbers=[], hours={},
    ))
    pg_db_session.add(Provider(
        clinic_id='market-mall-denture', name='Soheil',
        title='Denturist', is_active=True,
    ))
    pg_db_session.flush()
    return pg_db_session


def test_get_config_returns_merged_json(pg_client, seeded_for_endpoint):
    resp = pg_client.get("/api/clinics/market-mall-denture/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "market-mall-denture"
    assert body["assistant_name"] == "Emma"
    assert body["routing"]["dids"] == ["+15874023579"]
    assert body["provider_names"] == ["Soheil"]


def test_get_config_404_for_unknown_clinic(pg_client, seeded_for_endpoint):
    resp = pg_client.get("/api/clinics/does-not-exist/config")
    assert resp.status_code == 404

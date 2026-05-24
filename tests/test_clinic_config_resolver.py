"""Server-side merge: practice_types ← clinics ← per-clinic override rows."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.postgres   # use the postgres marker added in Task 1 fixups


@pytest.fixture
def seeded(pg_db_session):
    from database.models import (
        Clinic, ClinicAiVoice, ClinicAiDisclosure, ClinicRouting,
        PracticeType, Provider, ClinicClosure,
    )
    pt = PracticeType(
        id='denturist',
        assistant_name='Emma',
        ai_disclosure_required=True,
        ai_disclosure_phrase="I'm a virtual receptionist",
        greeting_message='base greeting',
        pricing_preface='preface',
        pricing_dentures_range='1700-2200',
        treatment_steps_guardrail='guardrail',
        triage_questions=['q1', 'q2'],
        default_feature_flags={'sms_notifications': True, 'ai_disclosure_v2': False},
    )
    pg_db_session.add(pt)
    clinic = Clinic(
        id='clinic-a',
        name='Clinic A',
        timezone='America/Edmonton',
        address='123 Main',
        contact_phone='+15870000000',
        practice_type_id='denturist',
        knowledge_base_path='kb/clinic-a',
        general_consultation_service_id=None,
        feature_flags_overrides={'ai_disclosure_v2': True},
    )
    pg_db_session.add(clinic)
    pg_db_session.add(ClinicRouting(
        clinic_id='clinic-a',
        ring_timeout_seconds=20,
        ai_after_hours=True, ai_in_hours_overflow=True,
        backup_number='+15879999999',
        ai_sip_uri='sip:test@example.com',
        dids=['+15871234567'],
        front_desk_numbers=[],
        hours={'mon': {'open': '09:00', 'close': '17:00'}},
    ))
    pg_db_session.add(Provider(clinic_id='clinic-a', name='Soheil', title='Denturist', is_active=True))
    pg_db_session.add(Provider(clinic_id='clinic-a', name='Nadeem', title='Denturist', is_active=True))
    # Flush the clinic + practice_type/routing/providers first so the FK from
    # clinic_closures.clinic_id resolves. SA's UoW does not reliably interleave
    # the PracticeType, Clinic, and ClinicClosure INSERTs in one flush against
    # the current model topology — splitting flushes is the simplest fix and
    # changes nothing about the resolver semantics being exercised.
    pg_db_session.flush()
    pg_db_session.add(ClinicClosure(
        id='cl-1', clinic_id='clinic-a',
        start_date='2026-12-25', end_date=None, kind='holiday',
    ))
    pg_db_session.flush()
    return pg_db_session


def test_resolve_returns_practice_type_defaults_when_no_override(seeded):
    from api.v1.clinics.resolver import resolve_clinic_config
    cfg = resolve_clinic_config(seeded, 'clinic-a')
    assert cfg['assistant_name'] == 'Emma'   # from practice_types
    assert cfg['ai_disclosure_phrase'] == "I'm a virtual receptionist"
    assert cfg['greeting_message'] == 'base greeting'
    assert cfg['triage_questions'] == ['q1', 'q2']


def test_resolve_clinic_ai_voice_overrides_practice_type(seeded):
    from database.models import ClinicAiVoice
    from api.v1.clinics.resolver import resolve_clinic_config
    seeded.add(ClinicAiVoice(
        clinic_id='clinic-a', assistant_name='Sophia',
        provider_title='Denturist', reason_question='What brings you in?',
        language='en',
    ))
    seeded.flush()
    cfg = resolve_clinic_config(seeded, 'clinic-a')
    assert cfg['assistant_name'] == 'Sophia'  # override wins


def test_resolve_feature_flags_merge(seeded):
    from api.v1.clinics.resolver import resolve_clinic_config
    cfg = resolve_clinic_config(seeded, 'clinic-a')
    # default_feature_flags: sms_notifications=True, ai_disclosure_v2=False
    # feature_flags_overrides:                       ai_disclosure_v2=True
    assert cfg['feature_flags']['sms_notifications'] is True
    assert cfg['feature_flags']['ai_disclosure_v2'] is True


def test_resolve_embeds_routing_block(seeded):
    from api.v1.clinics.resolver import resolve_clinic_config
    cfg = resolve_clinic_config(seeded, 'clinic-a')
    assert cfg['routing']['dids'] == ['+15871234567']
    assert cfg['routing']['ai_sip_uri'] == 'sip:test@example.com'
    assert cfg['routing']['holidays'] == ['2026-12-25']
    assert cfg['routing']['timezone'] == 'America/Edmonton'


def test_resolve_lists_active_providers(seeded):
    from api.v1.clinics.resolver import resolve_clinic_config
    cfg = resolve_clinic_config(seeded, 'clinic-a')
    assert sorted(cfg['provider_names']) == ['Nadeem', 'Soheil']


def test_resolve_returns_none_for_unknown_clinic(seeded):
    from api.v1.clinics.resolver import resolve_clinic_config
    assert resolve_clinic_config(seeded, 'does-not-exist') is None

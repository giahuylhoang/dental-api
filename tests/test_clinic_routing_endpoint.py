"""Contract tests for GET /api/clinics/{clinic_id}/routing."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.postgres


@pytest.fixture
def seeded_routing(pg_db_session):
    from database.models import Clinic, ClinicRouting, ClinicClosure
    pg_db_session.add(Clinic(id='clinic-x', name='X', timezone='America/Edmonton'))
    pg_db_session.flush()  # avoid SA UoW issue seen in Task 3
    pg_db_session.add(ClinicRouting(
        clinic_id='clinic-x',
        ring_timeout_seconds=18,
        ai_after_hours=False,
        ai_in_hours_overflow=True,
        backup_number='+15870000000',
        ai_sip_uri='sip:foo@bar',
        dids=['+15871234567'],
        front_desk_numbers=['+15879999999'],
        hours={'mon': {'open': '09:00', 'close': '17:00'}},
    ))
    pg_db_session.add(ClinicClosure(
        id='h1', clinic_id='clinic-x',
        start_date='2026-12-25', end_date=None, kind='holiday',
    ))
    pg_db_session.flush()
    return pg_db_session


def test_get_routing_returns_full_block(pg_client, seeded_routing):
    resp = pg_client.get("/api/clinics/clinic-x/routing")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dids"] == ["+15871234567"]
    assert body["ai_sip_uri"] == "sip:foo@bar"
    assert body["ai_after_hours"] is False
    assert body["holidays"] == ["2026-12-25"]
    assert body["hours"]["mon"] == {"open": "09:00", "close": "17:00"}


def test_get_routing_404_for_unknown_clinic(pg_client, seeded_routing):
    resp = pg_client.get("/api/clinics/missing/routing")
    assert resp.status_code == 404


def test_by_did_finds_clinic(pg_client, seeded_routing):
    resp = pg_client.get("/api/clinics/by-did/+15871234567")
    assert resp.status_code == 200
    assert resp.json() == {"clinic_id": "clinic-x"}


def test_by_did_normalizes_input(pg_client, seeded_routing):
    """Whitespace, parens, dashes get stripped to +digits before lookup."""
    resp = pg_client.get("/api/clinics/by-did/%2B1%20(587)%20123-4567")  # url-encoded "+1 (587) 123-4567"
    assert resp.status_code == 200
    assert resp.json() == {"clinic_id": "clinic-x"}


def test_by_did_404_for_unknown(pg_client, seeded_routing):
    resp = pg_client.get("/api/clinics/by-did/+19999999999")
    assert resp.status_code == 404

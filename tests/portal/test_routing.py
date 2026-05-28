"""Tests for /api/portal/clinics/{cid}/routing.

clinic_routing uses Postgres-native TEXT[] columns; tests run under pg_client.
"""

from datetime import date

import pytest

from api.main import app
from api.portal.deps import PortalUser, get_portal_user
from database.auth.memberships import UserClinicMembership
from database.models import ClinicRouting
from database.v1_1.models import ClinicClosure


def _seed_user(pg_db_session, uid="r-uid", clinic_ids=("t_clinic",)):
    """Install a PortalUser override + seed memberships for routing tests.

    The default tests/portal/conftest.py override_portal_user is bound to
    the SQLite db_session; routing tests use pg_db_session so we wire the
    pieces manually.
    """
    fake_user = PortalUser(
        uid=uid, email="r@x", clinic_ids=list(clinic_ids), role="admin",
    )
    app.dependency_overrides[get_portal_user] = lambda: fake_user
    for cid in clinic_ids:
        pg_db_session.add(UserClinicMembership(
            uid=uid, clinic_id=cid, email="r@x",
        ))
    pg_db_session.commit()


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    app.dependency_overrides.pop(get_portal_user, None)


def test_get_routing_empty_returns_defaults(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    r = pg_client.get("/api/portal/clinics/t_clinic/routing")
    assert r.status_code == 200
    body = r.json()
    assert body["timezone"] == "America/Edmonton"  # Clinic default
    assert body["dids"] == []
    assert body["front_desk_numbers"] == []
    assert body["ring_timeout_seconds"] == 20
    assert body["hours"] == {}
    assert body["holidays"] == []
    assert body["ai_after_hours"] is True
    assert body["ai_in_hours_overflow"] is True
    assert body["backup_number"] is None
    assert body["ai_sip_uri"] is None


def test_get_routing_projects_clinic_routing_correctly(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    pg_db_session.add(ClinicRouting(
        clinic_id="t_clinic",
        ring_timeout_seconds=5,
        ai_after_hours=False,
        ai_in_hours_overflow=False,
        backup_number="+13682990900",
        ai_sip_uri="sip:34.130.210.160:5060",
        dids=["+15874023579"],
        front_desk_numbers=["+14032476222"],
        hours={"mon": {"open": "09:00", "close": "17:00"}},
    ))
    pg_db_session.add(ClinicClosure(
        clinic_id="t_clinic", start_date=date(2026, 5, 18), kind="holiday",
    ))
    pg_db_session.commit()
    body = pg_client.get("/api/portal/clinics/t_clinic/routing").json()
    assert body["ring_timeout_seconds"] == 5
    assert body["dids"] == ["+15874023579"]
    assert body["front_desk_numbers"] == ["+14032476222"]
    assert body["hours"] == {"mon": {"open": "09:00", "close": "17:00"}}
    assert body["holidays"] == ["2026-05-18"]
    assert body["backup_number"] == "+13682990900"
    assert body["ai_sip_uri"] == "sip:34.130.210.160:5060"


def test_get_routing_skips_multi_day_closures(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    pg_db_session.add(ClinicClosure(
        clinic_id="t_clinic", start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3), kind="holiday",
    ))
    pg_db_session.add(ClinicClosure(
        clinic_id="t_clinic", start_date=date(2026, 6, 5),
        end_date=None, kind="holiday",
    ))
    pg_db_session.commit()
    body = pg_client.get("/api/portal/clinics/t_clinic/routing").json()
    # Multi-day skipped, single-day kept
    assert body["holidays"] == ["2026-06-05"]


def test_put_routing_upserts_clinic_routing(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    body = {
        "timezone": "America/Edmonton",
        "dids": ["+15870000001"],
        "front_desk_numbers": ["+15870000002"],
        "ring_timeout_seconds": 30,
        "hours": {"mon": {"open": "10:00", "close": "16:00"}},
        "holidays": [],
        "ai_after_hours": False,
        "ai_in_hours_overflow": True,
        "backup_number": None,
        "ai_sip_uri": None,
    }
    r = pg_client.put("/api/portal/clinics/t_clinic/routing", json=body)
    assert r.status_code == 200
    row = pg_db_session.query(ClinicRouting).filter_by(clinic_id="t_clinic").first()
    assert row is not None
    assert list(row.dids) == ["+15870000001"]
    assert row.ring_timeout_seconds == 30
    assert row.ai_after_hours is False
    assert row.hours == {"mon": {"open": "10:00", "close": "16:00"}}


def test_put_routing_replaces_single_day_holiday_closures(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    pg_db_session.add(ClinicClosure(
        clinic_id="t_clinic", start_date=date(2026, 5, 18), kind="holiday",
    ))
    pg_db_session.add(ClinicClosure(
        clinic_id="t_clinic", start_date=date(2026, 5, 25),
        end_date=date(2026, 5, 27), kind="holiday",  # multi-day, must survive
    ))
    pg_db_session.commit()
    body = {
        "timezone": "America/Edmonton",
        "holidays": ["2026-12-25", "2026-12-26"],
    }
    pg_client.put("/api/portal/clinics/t_clinic/routing", json=body)
    rows = pg_db_session.query(ClinicClosure).filter_by(
        clinic_id="t_clinic", kind="holiday").order_by(ClinicClosure.start_date).all()
    dates = [(r.start_date.isoformat(), r.end_date.isoformat() if r.end_date else None)
             for r in rows]
    # Multi-day preserved (2026-05-25..27); single-day replaced (12-25, 12-26)
    assert ("2026-05-25", "2026-05-27") in dates
    assert ("2026-12-25", None) in dates
    assert ("2026-12-26", None) in dates
    assert ("2026-05-18", None) not in dates       # old single-day gone


def test_put_routing_updates_clinic_timezone(pg_client, pg_db_session):
    from database.models import Clinic
    _seed_user(pg_db_session)
    body = {"timezone": "America/Toronto"}
    pg_client.put("/api/portal/clinics/t_clinic/routing", json=body)
    pg_db_session.expire_all()
    clinic = pg_db_session.query(Clinic).filter_by(id="t_clinic").first()
    assert clinic.timezone == "America/Toronto"


def test_put_routing_round_trips_via_get(pg_client, pg_db_session):
    _seed_user(pg_db_session)
    body = {
        "timezone": "America/Edmonton",
        "dids": ["+15870001111"],
        "front_desk_numbers": ["+15870002222"],
        "ring_timeout_seconds": 15,
        "hours": {"fri": {"open": "08:00", "close": "20:00"}},
        "holidays": ["2026-07-04"],
        "ai_after_hours": True,
        "ai_in_hours_overflow": False,
        "backup_number": "+15873334444",
        "ai_sip_uri": "sip:test:5060",
    }
    put_resp = pg_client.put("/api/portal/clinics/t_clinic/routing", json=body).json()
    get_resp = pg_client.get("/api/portal/clinics/t_clinic/routing").json()
    assert put_resp == get_resp
    assert get_resp["holidays"] == ["2026-07-04"]
    assert get_resp["ring_timeout_seconds"] == 15


def test_cross_clinic_blocked_via_membership(pg_client, pg_db_session):
    # User has membership for t_clinic only; deny request to a different clinic.
    _seed_user(pg_db_session, clinic_ids=["t_clinic"])
    r = pg_client.get("/api/portal/clinics/some-other-clinic/routing")
    assert r.status_code == 403

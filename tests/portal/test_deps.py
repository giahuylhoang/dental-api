"""Tests for /api/portal/* auth dependencies."""

import logging

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.portal.deps import get_portal_user
from database.auth.memberships import UserClinicMembership

client = TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_portal_user_override():
    """Pop any `get_portal_user` override after each test.

    Tests that manually install `app.dependency_overrides[get_portal_user]`
    (instead of going through the `override_portal_user` fixture) would
    otherwise leak the override into the next test in the module — masking
    `test_whoami_returns_401_without_token` under randomized order and
    leaking into other portal test modules in the same pytest session.
    """
    yield
    app.dependency_overrides.pop(get_portal_user, None)


def test_whoami_returns_401_without_token():
    r = client.get("/api/portal/whoami")
    assert r.status_code == 401


def test_whoami_returns_user_when_override_installed(override_portal_user):
    override_portal_user(uid="u1", email="a@b.com", clinic_ids=["default"], role="admin")
    r = client.get("/api/portal/whoami")
    assert r.status_code == 200
    body = r.json()
    assert body["uid"] == "u1"
    assert body["clinic_ids"] == ["default"]
    assert body["role"] == "admin"


def test_get_portal_user_does_not_403_when_clinic_ids_claim_missing(monkeypatch):
    """A user provisioned only via the membership table (no Firebase custom
    claim yet) must still reach require_clinic_access for the DB lookup.
    Pre-cutover behavior was to 403 here on missing clinic_ids — that gated
    out DB-canonical users and broke the soft-fallback design."""
    from api.portal import deps as portal_deps

    # Stub fb_auth.verify_id_token to return a decoded token without clinic_ids
    monkeypatch.setattr(portal_deps, "_ensure_app", lambda: None)
    fake_decoded = {"uid": "u-noclaim", "email": "n@x"}
    monkeypatch.setattr(
        portal_deps.fb_auth, "verify_id_token", lambda token: fake_decoded,
    )

    user = portal_deps.get_portal_user(authorization="Bearer dummy")
    assert user.uid == "u-noclaim"
    assert user.clinic_ids == []
    assert user.role == "readonly"


def test_require_clinic_access_with_membership_row_allows(
    db_session, override_portal_user, portal_user_factory,
):
    """DB row present, token claim absent → allow."""
    # Seed the membership row via the fixture (which uses clinic_ids=["default"]),
    # then swap in a PortalUser whose token claim is EMPTY so we know the DB row
    # is what's granting access.
    override_portal_user(uid="u-db", email="u@x", clinic_ids=["default"])
    no_claim_user = portal_user_factory(uid="u-db", email="u@x", clinic_ids=[])
    app.dependency_overrides[get_portal_user] = lambda: no_claim_user

    r = client.get("/api/portal/clinics/default/calls")
    assert r.status_code == 200


def test_require_clinic_access_no_row_but_token_claim_allows_with_warn(
    db_session, portal_user_factory, caplog,
):
    """No DB row, token claim grants access → allow + WARN logged."""
    fake_user = portal_user_factory(uid="u-fallback", email="u@x", clinic_ids=["default"])
    app.dependency_overrides[get_portal_user] = lambda: fake_user

    # Sanity-check there is no membership row for u-fallback yet.
    assert db_session.query(UserClinicMembership).filter_by(uid="u-fallback").count() == 0

    with caplog.at_level(logging.WARNING):
        r = client.get("/api/portal/clinics/default/calls")

    assert r.status_code == 200
    assert any("portal_membership_missing" in record.message for record in caplog.records)


def test_require_clinic_access_no_row_no_claim_403(portal_user_factory):
    """No DB row, no claim → 403."""
    fake_user = portal_user_factory(uid="u-denied", email="u@x", clinic_ids=[])
    app.dependency_overrides[get_portal_user] = lambda: fake_user

    r = client.get("/api/portal/clinics/default/calls")
    assert r.status_code == 403
    assert "no_access_to_clinic:default" in r.json()["detail"]


def test_require_clinic_access_stale_claim_with_no_row_still_allows_during_cutover(
    db_session, portal_user_factory, caplog,
):
    """A user whose membership was 'revoked' (no row) but whose token still
    has the stale claim keeps access during the cutover window. This documents
    the intentional trade-off — once the fallback is removed, revocation
    becomes immediate."""
    fake_user = portal_user_factory(uid="u-stale", email="u@x", clinic_ids=["default"])
    app.dependency_overrides[get_portal_user] = lambda: fake_user

    assert db_session.query(UserClinicMembership).filter_by(uid="u-stale").count() == 0

    with caplog.at_level(logging.WARNING):
        r = client.get("/api/portal/clinics/default/calls")

    assert r.status_code == 200
    assert any("portal_membership_missing" in record.message for record in caplog.records)

"""Shared portal test fixtures.

Provides:
- `override_portal_user` — install a fake authenticated PortalUser for the test
- `portal_db` (autouse) — point `get_db` at the in-memory SQLite session and
  seed the DEFAULT clinic so FK-constrained portal routes work

Both are autouse-friendly. Test files only need to use the `db_session` parent
fixture (from the root conftest) when they want to seed extra rows directly.
"""

import pytest

from api.main import app
from api.portal.deps import PortalUser, get_portal_user
from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID


@pytest.fixture
def portal_user_factory():
    def _make(uid="test-uid", email="t@example.com", clinic_ids=("default",), role="admin"):
        return PortalUser(uid=uid, email=email, clinic_ids=list(clinic_ids), role=role)
    return _make


@pytest.fixture
def override_portal_user(portal_user_factory, db_session):
    """Swap the authenticated PortalUser AND seed UserClinicMembership rows.

    Whatever clinic_ids are passed to the swap callable are written to the
    user_clinic_memberships table for the same uid, so the DB-backed gate
    introduced in 2026-05-28-admin-portal-auth-design picks the user up
    without each test having to seed memberships manually.
    """
    from database.auth.memberships import UserClinicMembership

    installed = {"current": portal_user_factory()}

    def _override():
        return installed["current"]

    app.dependency_overrides[get_portal_user] = _override

    def _seed_memberships(user):
        # Clear prior rows for this uid before re-seeding so the DB stays in
        # sync with the most recent _swap intent. Without this, a test that
        # calls override_portal_user(clinic_ids=["other"]) after the initial
        # default seed would still have "default" in the DB — silently
        # weakening any cross-clinic 403 assertion that uses "default" as the
        # negative case.
        db_session.query(UserClinicMembership).filter_by(uid=user.uid).delete()
        for cid in user.clinic_ids:
            db_session.add(UserClinicMembership(
                uid=user.uid, clinic_id=cid, email=user.email or "",
            ))
        db_session.commit()

    # Seed defaults from the initial PortalUser.
    _seed_memberships(installed["current"])

    def _swap(**kwargs):
        installed["current"] = portal_user_factory(**kwargs)
        _seed_memberships(installed["current"])

    yield _swap

    app.dependency_overrides.pop(get_portal_user, None)


@pytest.fixture(autouse=True)
def portal_db(db_session):
    """Route `get_db` at the in-memory SQLite session and seed the default clinic.

    Without this, portal tests would hit the real DATABASE_URL (likely a dev
    SQLite file) and leak state across runs. Seeding default clinic satisfies
    the FK on most portal tables.
    """
    if not db_session.query(Clinic).filter_by(id=DEFAULT_CLINIC_ID).first():
        db_session.add(Clinic(id=DEFAULT_CLINIC_ID, name="Default"))
        db_session.commit()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


# ── Smoke tests for the fixture itself ─────────────────────────────────

def test_override_portal_user_seeds_memberships(db_session, override_portal_user):
    """override_portal_user(clinic_ids=...) must seed both the PortalUser's
    clinic_ids field AND a UserClinicMembership row per clinic id, so the
    portal route's DB-based gate (Task 3) finds the user."""
    from database.auth.memberships import UserClinicMembership
    from database.models import Clinic

    # Seed a second clinic so the membership FK is satisfied.
    # SQLite doesn't enforce FK by default, but this keeps the test honest
    # in case foreign_keys=ON is enabled later.
    if not db_session.query(Clinic).filter_by(id="northeast-denture-clinic").first():
        db_session.add(Clinic(id="northeast-denture-clinic", name="NEDC"))
        db_session.commit()

    override_portal_user(uid="u-smoke", clinic_ids=["default", "northeast-denture-clinic"])

    rows = db_session.query(UserClinicMembership).filter_by(uid="u-smoke").all()
    assert {r.clinic_id for r in rows} == {"default", "northeast-denture-clinic"}

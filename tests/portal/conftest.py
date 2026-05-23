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
def override_portal_user(portal_user_factory):
    installed = {"current": portal_user_factory()}

    def _override():
        return installed["current"]

    app.dependency_overrides[get_portal_user] = _override

    def _swap(**kwargs):
        installed["current"] = portal_user_factory(**kwargs)

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

"""Shared portal test fixtures: Firebase auth override."""

import pytest

from api.main import app
from api.portal.deps import PortalUser, get_portal_user


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

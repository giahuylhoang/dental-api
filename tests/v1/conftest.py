"""v1 test fixtures: route get_db at the in-memory session and seed default clinic.

The parent tests/conftest.py provides db_session/client fixtures but only the
`client` fixture installs the get_db override. Tests in this folder instantiate
their own TestClient(app), so we need an autouse override mirroring the portal
conftest pattern.
"""

import pytest

from api.main import app
from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID


@pytest.fixture(autouse=True)
def _v1_db_override(db_session):
    if not db_session.query(Clinic).filter_by(id=DEFAULT_CLINIC_ID).first():
        db_session.add(Clinic(id=DEFAULT_CLINIC_ID, name="Default"))
        db_session.commit()

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)

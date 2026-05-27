"""Unit tests for engine.resolve_providers."""
import pytest

from database.models import Clinic, Provider
from services.slot_engine.engine import resolve_providers


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    soheil = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    nadeem = Provider(clinic_id="c1", name="Nadeem", title="Denturist", is_active=True)
    inactive = Provider(clinic_id="c1", name="Old", title="Denturist", is_active=False)
    db_session.add_all([c, soheil, nadeem, inactive])
    db_session.commit()
    return soheil, nadeem


def test_none_provided_returns_all_active(db_session, setup):
    soheil, nadeem = setup
    out = resolve_providers("c1", None, None, db_session)
    names = sorted(p.name for p in out)
    assert names == ["Nadeem", "Soheil"]


def test_provider_id_match(db_session, setup):
    soheil, _ = setup
    out = resolve_providers("c1", soheil.id, None, db_session)
    assert [p.name for p in out] == ["Soheil"]


def test_provider_id_no_match_returns_empty(db_session, setup):
    out = resolve_providers("c1", 9999, None, db_session)
    assert out == []


def test_provider_name_partial_case_insensitive(db_session, setup):
    out = resolve_providers("c1", None, "soh", db_session)
    assert [p.name for p in out] == ["Soheil"]


def test_provider_name_no_match_returns_empty(db_session, setup):
    out = resolve_providers("c1", None, "nobody", db_session)
    assert out == []


def test_inactive_providers_excluded(db_session, setup):
    out = resolve_providers("c1", None, "Old", db_session)
    assert out == []

"""Unit tests for scripts/grant_clinic_access.py."""
from unittest.mock import MagicMock, patch

import pytest

from database.auth import UserClinicMembership
from database.models import Clinic


@pytest.fixture
def seed_clinics(db_session):
    db_session.add(Clinic(id="market-mall-denture", name="Market Mall"))
    db_session.add(Clinic(id="northeast-denture-clinic", name="North East"))
    db_session.commit()


def _fake_firebase_user(uid="u-123", email="alice@example.com"):
    user = MagicMock()
    user.uid = uid
    user.email = email
    return user


def test_grant_creates_membership_rows(seed_clinics, db_session):
    from scripts.grant_clinic_access import grant

    with patch("scripts.grant_clinic_access._ensure_firebase_user",
               return_value=_fake_firebase_user()):
        result = grant(
            db=db_session,
            email="alice@example.com",
            password="OneTime123!",
            clinic_ids=["market-mall-denture", "northeast-denture-clinic"],
        )
    assert result["uid"] == "u-123"
    rows = db_session.query(UserClinicMembership).filter_by(uid="u-123").all()
    assert sorted(r.clinic_id for r in rows) == [
        "market-mall-denture",
        "northeast-denture-clinic",
    ]


def test_grant_is_idempotent(seed_clinics, db_session):
    from scripts.grant_clinic_access import grant

    with patch("scripts.grant_clinic_access._ensure_firebase_user",
               return_value=_fake_firebase_user()):
        grant(db=db_session, email="a@x.com", password="x", clinic_ids=["market-mall-denture"])
        grant(db=db_session, email="a@x.com", password="x", clinic_ids=["market-mall-denture"])
    rows = db_session.query(UserClinicMembership).filter_by(uid="u-123").all()
    assert len(rows) == 1


def test_grant_rejects_unknown_clinic(seed_clinics, db_session):
    from scripts.grant_clinic_access import grant, UnknownClinicError

    with patch("scripts.grant_clinic_access._ensure_firebase_user",
               return_value=_fake_firebase_user()):
        with pytest.raises(UnknownClinicError):
            grant(db=db_session, email="a@x.com", password="x", clinic_ids=["does-not-exist"])


def test_revoke_removes_only_specified_clinic(seed_clinics, db_session):
    from scripts.grant_clinic_access import grant, revoke

    with patch("scripts.grant_clinic_access._ensure_firebase_user",
               return_value=_fake_firebase_user()):
        grant(
            db=db_session,
            email="a@x.com",
            password="x",
            clinic_ids=["market-mall-denture", "northeast-denture-clinic"],
        )
        revoke(db=db_session, uid="u-123", clinic_ids=["market-mall-denture"])

    remaining = [r.clinic_id for r in db_session.query(UserClinicMembership).filter_by(uid="u-123").all()]
    assert remaining == ["northeast-denture-clinic"]


def test_list_memberships_for_uid(seed_clinics, db_session):
    from scripts.grant_clinic_access import grant, list_memberships

    with patch("scripts.grant_clinic_access._ensure_firebase_user",
               return_value=_fake_firebase_user()):
        grant(
            db=db_session,
            email="a@x.com",
            password="x",
            clinic_ids=["market-mall-denture", "northeast-denture-clinic"],
        )
    out = list_memberships(db=db_session, uid="u-123")
    assert sorted(out) == ["market-mall-denture", "northeast-denture-clinic"]

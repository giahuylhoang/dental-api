"""Unit tests for api/dependencies/auth.py."""
import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.dependencies.auth import (
    get_current_uid,
    get_authorized_clinic,
    get_internal_caller,
)


# ---------------- get_current_uid ----------------

def test_current_uid_bypass_returns_dev_uid(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", True)
    assert get_current_uid(authorization=None) == "dev-skip-uid"


def test_current_uid_missing_header_raises_401(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with pytest.raises(HTTPException) as exc:
        get_current_uid(authorization=None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "missing_token"


def test_current_uid_malformed_header_raises_401(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with pytest.raises(HTTPException) as exc:
        get_current_uid(authorization="NotBearer xyz")
    assert exc.value.status_code == 401
    assert exc.value.detail == "missing_token"


def test_current_uid_invalid_token_raises_401(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with patch("api.dependencies.auth.firebase_auth.verify_id_token", side_effect=ValueError("bad")):
        with pytest.raises(HTTPException) as exc:
            get_current_uid(authorization="Bearer junk")
    assert exc.value.status_code == 401
    assert exc.value.detail == "invalid_token"


def test_current_uid_valid_token_returns_uid(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with patch(
        "api.dependencies.auth.firebase_auth.verify_id_token",
        return_value={"uid": "user-abc"},
    ):
        assert get_current_uid(authorization="Bearer goodtoken") == "user-abc"


# ---------------- get_authorized_clinic ----------------

def test_authorized_clinic_bypass_returns_any_existing_clinic(db_session, monkeypatch):
    """In bypass mode, only existence is checked — no membership lookup."""
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", True)
    from database.models import Clinic
    db_session.add(Clinic(id="default", name="Default Clinic"))
    db_session.commit()
    clinic = get_authorized_clinic(uid="anyone", x_clinic_id="default", db=db_session)
    assert clinic.id == "default"


def test_authorized_clinic_rejects_clinic_not_in_membership(db_session, monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    from database.models import Clinic
    from database.auth import UserClinicMembership
    db_session.add(Clinic(id="market-mall-denture", name="Market Mall"))
    db_session.add(UserClinicMembership(
        uid="user-1", clinic_id="market-mall-denture", email="a@x.com",
    ))
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        get_authorized_clinic(uid="user-1", x_clinic_id="northeast-denture-clinic", db=db_session)
    assert exc.value.status_code == 403
    assert exc.value.detail == "clinic_forbidden"


def test_authorized_clinic_allows_membership_match(db_session, monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    from database.models import Clinic
    from database.auth import UserClinicMembership
    db_session.add(Clinic(id="market-mall-denture", name="Market Mall"))
    db_session.add(UserClinicMembership(
        uid="user-1", clinic_id="market-mall-denture", email="a@x.com",
    ))
    db_session.commit()
    clinic = get_authorized_clinic(uid="user-1", x_clinic_id="market-mall-denture", db=db_session)
    assert clinic.id == "market-mall-denture"


# ---------------- get_internal_caller ----------------

def test_internal_caller_rejects_missing_secret(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with pytest.raises(HTTPException) as exc:
        get_internal_caller(x_internal_secret=None)
    assert exc.value.status_code == 401


def test_internal_caller_rejects_wrong_secret(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    with pytest.raises(HTTPException) as exc:
        get_internal_caller(x_internal_secret="wrong")
    assert exc.value.status_code == 401


def test_internal_caller_accepts_correct_secret(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)
    # No raise = pass
    get_internal_caller(x_internal_secret="topsecret")


def test_internal_caller_bypass_short_circuits(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", True)
    get_internal_caller(x_internal_secret=None)  # no raise

"""End-to-end auth tests: simulate Firebase token verification + membership lookups."""
from unittest.mock import patch

import pytest

from database.auth import UserClinicMembership
from database.models import Clinic


@pytest.fixture
def auth_off(monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", False)


def _seed(db, *memberships):
    """memberships: list of (uid, clinic_id, email)."""
    seen_clinics = set()
    for uid, clinic_id, _ in memberships:
        if clinic_id not in seen_clinics:
            db.add(Clinic(id=clinic_id, name=clinic_id))
            seen_clinics.add(clinic_id)
    for uid, clinic_id, email in memberships:
        db.add(UserClinicMembership(uid=uid, clinic_id=clinic_id, email=email))
    db.commit()


def test_no_token_returns_401(client, db_session, auth_off):
    resp = client.get("/api/clinics/me", headers={"X-Clinic-Id": "anything"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "missing_token"


def test_invalid_token_returns_401(client, db_session, auth_off):
    with patch(
        "api.dependencies.auth.firebase_auth.verify_id_token",
        side_effect=ValueError("bad"),
    ):
        resp = client.get(
            "/api/clinics/me",
            headers={"Authorization": "Bearer junk", "X-Clinic-Id": "default"},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_token"


def test_valid_token_but_no_membership_returns_403(client, db_session, auth_off):
    _seed(db_session, ("other-user", "market-mall-denture", "o@x.com"))
    with patch(
        "api.dependencies.auth.firebase_auth.verify_id_token",
        return_value={"uid": "user-without-access"},
    ):
        resp = client.get(
            "/api/clinics/me",
            headers={
                "Authorization": "Bearer good",
                "X-Clinic-Id": "market-mall-denture",
            },
        )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "clinic_forbidden"


def test_valid_token_with_membership_succeeds(client, db_session, auth_off):
    _seed(db_session, ("user-1", "market-mall-denture", "u1@x.com"))
    with patch(
        "api.dependencies.auth.firebase_auth.verify_id_token",
        return_value={"uid": "user-1"},
    ):
        resp = client.get(
            "/api/clinics/me",
            headers={
                "Authorization": "Bearer good",
                "X-Clinic-Id": "market-mall-denture",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["id"] == "market-mall-denture"


def test_multi_clinic_user_sees_both_in_list(client, db_session, auth_off):
    _seed(
        db_session,
        ("user-multi", "market-mall-denture", "m@x.com"),
        ("user-multi", "northeast-denture-clinic", "m@x.com"),
    )
    with patch(
        "api.dependencies.auth.firebase_auth.verify_id_token",
        return_value={"uid": "user-multi"},
    ):
        resp = client.get("/api/clinics", headers={"Authorization": "Bearer good"})
    assert resp.status_code == 200
    ids = sorted(c["id"] for c in resp.json()["clinics"])
    assert ids == ["market-mall-denture", "northeast-denture-clinic"]


def test_internal_endpoint_rejects_missing_secret(client, db_session, auth_off, monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    resp = client.get("/api/clinics/default/config")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "internal_auth_failed"


def test_internal_endpoint_accepts_correct_secret(client, db_session, auth_off, monkeypatch):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "topsecret")
    # Use a clinic_id that doesn't exist. The internal-secret check happens
    # BEFORE resolve_clinic_config; a missing clinic yields 404, which means
    # auth passed. We avoid `default` because the conftest seeds it (causing
    # a UNIQUE collision) and accessing its lazy `routing` relationship
    # would crash on SQLite (clinic_routing is in _SQLITE_SKIP_TABLES).
    resp = client.get(
        "/api/clinics/nonexistent-clinic/config",
        headers={"X-Internal-Secret": "topsecret"},
    )
    # Auth passed if we got past 401. 404 = clinic not found, exactly what we want.
    assert resp.status_code == 404

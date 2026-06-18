"""Tests for scripts/backfill_portal_memberships.py — one-shot Firebase →
user_clinic_memberships migration utility."""

from types import SimpleNamespace

import pytest

from database.auth.memberships import UserClinicMembership


def _fake_user(uid, email, clinic_ids):
    return SimpleNamespace(uid=uid, email=email, custom_claims={"clinic_ids": clinic_ids})


def _patch_list_users(monkeypatch, users):
    """Stub firebase_admin.auth.list_users() to yield a fake iterator page."""
    fake_page = SimpleNamespace(iterate_all=lambda: iter(users))
    import scripts.backfill_portal_memberships as backfill_mod
    monkeypatch.setattr(backfill_mod, "list_users", lambda: fake_page)


def test_backfill_inserts_one_row_per_clinic_claim(monkeypatch, db_session):
    from scripts.backfill_portal_memberships import run_backfill
    _patch_list_users(monkeypatch, [
        _fake_user("u1", "u1@x", ["default", "market-mall-denture"]),
    ])

    summary = run_backfill(db_session)

    rows = db_session.query(UserClinicMembership).filter_by(uid="u1").all()
    assert {r.clinic_id for r in rows} == {"default", "market-mall-denture"}
    assert summary["rows_inserted"] == 2
    assert summary["users_scanned"] == 1
    assert summary["users_without_claim"] == 0


def test_backfill_is_idempotent(monkeypatch, db_session):
    from scripts.backfill_portal_memberships import run_backfill
    _patch_list_users(monkeypatch, [_fake_user("u2", "u2@x", ["default"])])

    first = run_backfill(db_session)
    second = run_backfill(db_session)

    rows = db_session.query(UserClinicMembership).filter_by(uid="u2").all()
    assert len(rows) == 1                    # not duplicated
    assert first["rows_inserted"] == 1
    assert second["rows_inserted"] == 0
    assert second["rows_skipped_existing"] == 1


def test_backfill_skips_users_without_clinic_claim(monkeypatch, db_session):
    from scripts.backfill_portal_memberships import run_backfill
    _patch_list_users(monkeypatch, [
        _fake_user("u3", "u3@x", []),                    # empty list
        SimpleNamespace(uid="u4", email="u4@x", custom_claims=None),  # no claims at all
    ])

    summary = run_backfill(db_session)

    assert db_session.query(UserClinicMembership).count() == 0
    assert summary["users_without_claim"] == 2
    assert summary["rows_inserted"] == 0

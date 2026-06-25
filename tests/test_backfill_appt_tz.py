"""Unit tests for scripts/backfill_appt_tz.py (Task 2.4, Steps 1-2 only).

These exercise the DST-aware, source-scoped offset logic on the SQLite fixture.
NO production database is touched here — the script's prod run (backup, dry-run,
--apply) is a separately gated step and is intentionally NOT executed.
"""
import json
import os
from datetime import datetime, time, timezone

import pytest

from database.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    Patient,
    Provider,
)
from scripts.backfill_appt_tz import (
    CANDIDATE_SOURCES,
    PROTECTED_SOURCES,
    apply_backfill,
    compute_backfill_diffs,
    count_protected,
    main,
    offset_minutes,
)


# ---------------------------------------------------------------------------
# offset_minutes — DST-aware signed UTC offset for a clinic-local wall-clock.
# ---------------------------------------------------------------------------


def test_offset_minutes_edmonton_summer_is_minus_360():
    assert offset_minutes("America/Edmonton", datetime(2026, 6, 25, 14, 0)) == -360


def test_offset_minutes_edmonton_winter_is_minus_420():
    assert offset_minutes("America/Edmonton", datetime(2026, 12, 25, 9, 0)) == -420


def test_offset_minutes_vancouver_summer_is_minus_420():
    assert offset_minutes("America/Vancouver", datetime(2026, 6, 25, 14, 0)) == -420


# ---------------------------------------------------------------------------
# compute_backfill_diffs + apply_backfill — scoping and DST-correct shift.
# ---------------------------------------------------------------------------


def _seed(db):
    db.add(Clinic(id="edm", name="Edmonton", timezone="America/Edmonton"))
    db.add(Clinic(id="van", name="Vancouver", timezone="America/Vancouver"))
    db.add(Provider(id=1, clinic_id="edm", name="A", title="Denturist", is_active=True))
    db.add(Provider(id=2, clinic_id="van", name="B", title="Denturist", is_active=True))
    db.add(Patient(id="pe", clinic_id="edm", first_name="E", last_name="P", phone="111"))
    db.add(Patient(id="pv", clinic_id="van", first_name="V", last_name="P", phone="222"))
    db.flush()

    def _appt(aid, clinic_id, provider_id, patient_id, source, y, mo, d, h):
        return Appointment(
            id=aid, clinic_id=clinic_id, provider_id=provider_id, patient_id=patient_id,
            start_time=datetime(y, mo, d, h, 0), end_time=datetime(y, mo, d, h + 1, 0),
            status=AppointmentStatus.SCHEDULED, source=source,
        )

    # candidate (source IS NULL), Edmonton summer 14:00 -> +6h -> 20:00
    db.add(_appt("a-summer", "edm", 1, "pe", None, 2026, 6, 25, 14))
    # candidate (booking-web-hold), Edmonton winter 09:00 -> +7h -> 16:00
    db.add(_appt("a-winter", "edm", 1, "pe", "booking-web-hold", 2026, 12, 25, 9))
    # PROTECTED voice-hold, must be skipped & unchanged
    db.add(_appt("a-voice", "edm", 1, "pe", "voice-hold", 2026, 6, 25, 14))
    # candidate, Vancouver summer 14:00 -> +7h (PDT) -> 21:00
    db.add(_appt("a-van", "van", 2, "pv", None, 2026, 6, 25, 14))
    db.commit()


def test_scope_excludes_voice_hold_and_includes_candidates(db_session):
    _seed(db_session)
    diffs = compute_backfill_diffs(db_session)
    ids = {d.appointment_id for d in diffs}
    assert ids == {"a-summer", "a-winter", "a-van"}
    assert "a-voice" not in ids


def test_diffs_compute_dst_correct_after_values(db_session):
    _seed(db_session)
    by_id = {d.appointment_id: d for d in compute_backfill_diffs(db_session)}

    assert by_id["a-summer"].start_after == datetime(2026, 6, 25, 20, 0)
    assert by_id["a-summer"].end_after == datetime(2026, 6, 25, 21, 0)
    assert by_id["a-winter"].start_after == datetime(2026, 12, 25, 16, 0)
    assert by_id["a-van"].start_after == datetime(2026, 6, 25, 21, 0)


def test_apply_backfill_shifts_candidates_and_protects_voice_hold(db_session, tmp_path):
    _seed(db_session)
    protected_before = count_protected(db_session)
    diffs = compute_backfill_diffs(db_session)
    apply_backfill(db_session, diffs, before=datetime(2026, 7, 1, 0, 0), audit_dir=str(tmp_path))

    summer = db_session.query(Appointment).filter_by(id="a-summer").one()
    winter = db_session.query(Appointment).filter_by(id="a-winter").one()
    van = db_session.query(Appointment).filter_by(id="a-van").one()
    voice = db_session.query(Appointment).filter_by(id="a-voice").one()

    assert summer.start_time == datetime(2026, 6, 25, 20, 0)
    assert summer.end_time == datetime(2026, 6, 25, 21, 0)
    assert winter.start_time == datetime(2026, 12, 25, 16, 0)
    assert van.start_time == datetime(2026, 6, 25, 21, 0)
    # voice-hold untouched.
    assert voice.start_time == datetime(2026, 6, 25, 14, 0)
    assert count_protected(db_session) == protected_before


def test_source_constants():
    assert None in CANDIDATE_SOURCES
    assert "booking-web-hold" in CANDIDATE_SOURCES
    assert PROTECTED_SOURCES == {"voice-hold"}


# ---------------------------------------------------------------------------
# Task 4 hardening: created_at cutoff, --apply validation, tripwire, audit.
# ---------------------------------------------------------------------------

CUTOFF = datetime(2026, 6, 24, 0, 0)  # boundary; pre-cutoff created, post excluded


def _set_created(db, aid, created_at):
    db.query(Appointment).filter_by(id=aid).update({"created_at": created_at})
    db.commit()


def test_cutoff_excludes_post_cutoff_candidate_row(db_session):
    _seed(db_session)
    # a-summer created AFTER the cutoff -> excluded
    _set_created(db_session, "a-summer", datetime(2026, 6, 25, 23, 0))
    # a-winter created BEFORE the cutoff -> included
    _set_created(db_session, "a-winter", datetime(2026, 6, 1, 0, 0))

    diffs = compute_backfill_diffs(db_session, before=CUTOFF)
    ids = {d.appointment_id for d in diffs}
    assert "a-summer" not in ids
    assert "a-winter" in ids


def test_cutoff_pre_cutoff_candidate_is_shifted(db_session, tmp_path):
    _seed(db_session)
    _set_created(db_session, "a-summer", datetime(2026, 6, 1, 0, 0))
    _set_created(db_session, "a-winter", datetime(2026, 6, 1, 0, 0))
    _set_created(db_session, "a-van", datetime(2026, 6, 1, 0, 0))

    diffs = compute_backfill_diffs(db_session, before=CUTOFF)
    apply_backfill(db_session, diffs, before=CUTOFF, audit_dir=str(tmp_path))

    summer = db_session.query(Appointment).filter_by(id="a-summer").one()
    assert summer.start_time == datetime(2026, 6, 25, 20, 0)


def test_apply_without_before_created_at_errors(db_session, monkeypatch):
    # --apply without --before-created-at must fail loudly (SystemExit, non-zero)
    # AND must never reach a DB write path.
    def _no_write(*a, **kw):
        raise AssertionError("apply_backfill must not be reached without --before-created-at")

    import scripts.backfill_appt_tz as mod

    monkeypatch.setattr(mod, "apply_backfill", _no_write)
    monkeypatch.setattr(
        "database.connection.SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("SessionLocal must not be touched")),
    )
    with pytest.raises(SystemExit) as exc:
        main(["--apply"])
    assert exc.value.code != 0


def test_diff_targeting_currently_protected_row_raises_runtime_error(db_session, tmp_path):
    _seed(db_session)
    diffs = compute_backfill_diffs(db_session)
    # Simulate a source flip between diff and apply: retarget a diff at the
    # protected voice-hold row.
    diffs[0].appointment_id = "a-voice"
    with __import__("pytest").raises(RuntimeError):
        apply_backfill(db_session, diffs, before=datetime(2026, 7, 1, 0, 0), audit_dir=str(tmp_path))


def test_protected_row_tamper_detected_after_apply(db_session, tmp_path):
    """If a protected row's timestamp changes between snapshot and verify
    (e.g. a concurrent writer), the tripwire raises RuntimeError."""
    _seed(db_session)

    # Monkeypatch db.commit so that, right after the real commit but before the
    # post-commit re-read, we tamper a protected voice-hold row's start_time.
    real_commit = db_session.commit
    tampered = {"done": False}

    def tampering_commit():
        real_commit()
        if not tampered["done"]:
            # Swap start_time <-> end_time keeps COUNT constant but changes values.
            v = db_session.query(Appointment).filter_by(id="a-voice").one()
            v.start_time, v.end_time = v.end_time, v.start_time
            real_commit()
            tampered["done"] = True

    db_session.commit = tampering_commit  # type: ignore[assignment]

    diffs = compute_backfill_diffs(db_session)
    with __import__("pytest").raises(RuntimeError):
        apply_backfill(db_session, diffs, before=datetime(2026, 7, 1, 0, 0), audit_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# Task 4 round 2: UTC-normalize cutoff, enforce in apply, durable audit file.
# ---------------------------------------------------------------------------

from scripts.backfill_appt_tz import _normalize_cutoff, _audit_path  # noqa: E402


# --- Fix 1: cutoff normalization to naive UTC ------------------------------


def test_normalize_cutoff_aware_converts_to_naive_utc():
    # 2026-06-25T00:00:00-06:00 (MDT) == 2026-06-25T06:00:00 UTC
    aware = datetime.fromisoformat("2026-06-25T00:00:00-06:00")
    out = _normalize_cutoff(aware)
    assert out.tzinfo is None
    assert out == datetime(2026, 6, 25, 6, 0, 0)


def test_normalize_cutoff_naive_passes_through():
    naive = datetime(2026, 6, 25, 6, 0, 0)
    out = _normalize_cutoff(naive)
    assert out.tzinfo is None
    assert out == naive


# --- Fix 2: apply_backfill enforces the cutoff -----------------------------


def test_apply_backfill_requires_before_not_none(db_session):
    _seed(db_session)
    diffs = compute_backfill_diffs(db_session)
    with pytest.raises(RuntimeError):
        apply_backfill(db_session, diffs, before=None)


def test_apply_backfill_refuses_post_cutoff_diff(db_session):
    """A diff whose row is at/after the cutoff must not be written; the whole
    batch is refused with a RuntimeError listing the offending id."""
    _seed(db_session)
    # a-summer created AFTER the cutoff.
    _set_created(db_session, "a-summer", datetime(2026, 6, 25, 23, 0))
    _set_created(db_session, "a-winter", datetime(2026, 6, 1, 0, 0))
    _set_created(db_session, "a-van", datetime(2026, 6, 1, 0, 0))

    before = datetime(2026, 6, 24, 0, 0)
    # Mix a post-cutoff diff (a-summer) into the batch.
    diffs = compute_backfill_diffs(db_session)  # unfiltered: includes a-summer
    assert any(d.appointment_id == "a-summer" for d in diffs)

    summer_before = db_session.query(Appointment).filter_by(id="a-summer").one().start_time
    with pytest.raises(RuntimeError) as exc:
        apply_backfill(db_session, diffs, before=before)
    assert "a-summer" in str(exc.value)
    # Nothing written.
    assert db_session.query(Appointment).filter_by(id="a-summer").one().start_time == summer_before
    assert db_session.query(Appointment).filter_by(id="a-winter").one().start_time == datetime(2026, 12, 25, 9, 0)


# --- Fix 3+4: durable audit file as idempotency marker ---------------------


def _apply_via_main(monkeypatch, db_session, tmp_path, before_iso, force=False):
    """Drive `main` against the SQLite session + tmp audit dir."""
    import scripts.backfill_appt_tz as mod

    monkeypatch.setattr("database.connection.SessionLocal", lambda: db_session)
    argv = ["--apply", "--before-created-at", before_iso, "--audit-dir", str(tmp_path)]
    if force:
        argv.append("--force")
    main(argv)


def test_apply_writes_audit_file_with_start_and_end_and_cutoff(db_session, monkeypatch, tmp_path):
    _seed(db_session)
    _set_created(db_session, "a-summer", datetime(2026, 6, 1, 0, 0))
    _set_created(db_session, "a-winter", datetime(2026, 6, 1, 0, 0))
    _set_created(db_session, "a-van", datetime(2026, 6, 1, 0, 0))

    before_iso = "2026-06-24T00:00:00"
    _apply_via_main(monkeypatch, db_session, tmp_path, before_iso)

    audit_path = _audit_path(tmp_path, _normalize_cutoff(datetime.fromisoformat(before_iso)))
    assert os.path.exists(audit_path), f"audit file missing at {audit_path}"
    data = json.loads(open(audit_path).read())

    assert data["cutoff"] == "2026-06-24T00:00:00"
    by_id = {e["id"]: e for e in data["rows"]}
    assert set(by_id) == {"a-summer", "a-winter", "a-van"}
    # Full start + end before/after present.
    summer = by_id["a-summer"]
    assert summer["start_before"].startswith("2026-06-25T14:00")
    assert summer["start_after"].startswith("2026-06-25T20:00")
    assert summer["end_before"].startswith("2026-06-25T15:00")
    assert summer["end_after"].startswith("2026-06-25T21:00")
    assert summer["source"] is None
    assert summer["clinic_tz"] == "America/Edmonton"
    assert summer["offset_minutes"] == -360
    assert "run_at" in data


def test_second_apply_with_same_cutoff_is_refused(db_session, monkeypatch, tmp_path, capsys):
    _seed(db_session)
    for aid in ("a-summer", "a-winter", "a-van"):
        _set_created(db_session, aid, datetime(2026, 6, 1, 0, 0))

    before_iso = "2026-06-24T00:00:00"
    _apply_via_main(monkeypatch, db_session, tmp_path, before_iso)  # first run ok
    audit_path = _audit_path(tmp_path, _normalize_cutoff(datetime.fromisoformat(before_iso)))
    assert os.path.exists(audit_path)

    # Second run with same cutoff must refuse (audit exists).
    with pytest.raises(SystemExit) as exc:
        _apply_via_main(monkeypatch, db_session, tmp_path, before_iso)
    assert exc.value.code != 0
    out = capsys.readouterr().out
    assert "already" in out.lower() or "refus" in out.lower()


def test_force_overrides_and_rewrites_audit(db_session, monkeypatch, tmp_path):
    _seed(db_session)
    for aid in ("a-summer", "a-winter", "a-van"):
        _set_created(db_session, aid, datetime(2026, 6, 1, 0, 0))

    before_iso = "2026-06-24T00:00:00"
    _apply_via_main(monkeypatch, db_session, tmp_path, before_iso)
    _apply_via_main(monkeypatch, db_session, tmp_path, before_iso, force=True)  # no raise
    audit_path = _audit_path(tmp_path, _normalize_cutoff(datetime.fromisoformat(before_iso)))
    assert os.path.exists(audit_path)
    data = json.loads(open(audit_path).read())
    assert len(data["rows"]) == 3


def test_audit_file_written_before_protected_verify(db_session, monkeypatch, tmp_path):
    """If the post-commit protected-verify trips, the audit file must already
    exist on disk with the committed shifts (full revert record)."""
    _seed(db_session)
    for aid in ("a-summer", "a-winter", "a-van"):
        _set_created(db_session, aid, datetime(2026, 6, 1, 0, 0))

    import scripts.backfill_appt_tz as mod

    real_verify = mod._verify_protected_unchanged

    def failing_verify(db, snapshot):
        # Assert audit file already written before this (would-be) tripwire.
        before_iso = "2026-06-24T00:00:00"
        audit_path = _audit_path(tmp_path, _normalize_cutoff(datetime.fromisoformat(before_iso)))
        assert os.path.exists(audit_path), "audit file must precede protected-verify"
        raise RuntimeError("simulated protected-verify failure")

    monkeypatch.setattr(mod, "_verify_protected_unchanged", failing_verify)
    monkeypatch.setattr("database.connection.SessionLocal", lambda: db_session)

    with pytest.raises(RuntimeError):
        main(["--apply", "--before-created-at", "2026-06-24T00:00:00",
              "--audit-dir", str(tmp_path)])

    before_iso = "2026-06-24T00:00:00"
    audit_path = _audit_path(tmp_path, _normalize_cutoff(datetime.fromisoformat(before_iso)))
    assert os.path.exists(audit_path)
    data = json.loads(open(audit_path).read())
    assert len(data["rows"]) == 3



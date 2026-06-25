"""Unit tests for scripts/backfill_appt_tz.py (Task 2.4, Steps 1-2 only).

These exercise the DST-aware, source-scoped offset logic on the SQLite fixture.
NO production database is touched here — the script's prod run (backup, dry-run,
--apply) is a separately gated step and is intentionally NOT executed.
"""
from datetime import datetime, time

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


def test_apply_backfill_shifts_candidates_and_protects_voice_hold(db_session):
    _seed(db_session)
    protected_before = count_protected(db_session)
    diffs = compute_backfill_diffs(db_session)
    apply_backfill(db_session, diffs)

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

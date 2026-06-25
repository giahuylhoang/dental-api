"""DST-aware, source-scoped backfill that repairs historically mis-stored
appointment timestamps (Task 2.4).

Background
----------
Before the 2026-06-25 timezone fix, CRM (`source IS NULL`) and Market-Mall
web-hold (`source='booking-web-hold'`) callers POSTed *naive clinic-local*
wall-clock times. The old write path stored them verbatim in the
`timestamp without time zone` columns, which are supposed to hold naive UTC.
A 2:00 PM Edmonton booking was therefore stored as `14:00` instead of `20:00`
(MDT) / `21:00` (MST) UTC, so it rendered 6-7 h early.

This script shifts each affected row FORWARD by its own clinic's UTC offset on
its own date (so DST is handled per-row via zoneinfo). It NEVER touches
`source='voice-hold'` rows — the voice agent always sent offset-aware times,
which Postgres stored as correct UTC.

Safety / gating
---------------
Steps 3-6 of the plan (Cloud SQL backup, prod dry-run, `--apply` against
production) are GATED and require an explicit "deploy now". This module only
authors the logic + a `--dry-run`/`--apply` CLI; the unit tests
(tests/test_backfill_appt_tz.py) exercise it on SQLite. Running it against any
real database is a separate, human-gated action.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from database.models import Appointment, Clinic

DEFAULT_TZ = "America/Edmonton"

# Source values whose rows were stored as naive clinic-local and must be shifted.
# `None` (CRM, no source set) and the Market-Mall web-hold channel.
CANDIDATE_SOURCES = {None, "booking-web-hold"}
# Never touch these — already correct UTC (voice agent sent offset-aware times).
PROTECTED_SOURCES = {"voice-hold"}


@dataclass
class BackfillDiff:
    appointment_id: str
    source: Optional[str]
    clinic_tz: str
    offset_minutes: int
    start_before: datetime
    start_after: datetime
    end_before: Optional[datetime]
    end_after: Optional[datetime]


def offset_minutes(clinic_tz: str, dt: datetime) -> int:
    """Signed UTC offset (in minutes) for a NAIVE clinic-local wall-clock `dt`
    in `clinic_tz`, DST-correct for that specific date.

    Edmonton summer (MDT) -> -360; Edmonton winter (MST) -> -420;
    Vancouver summer (PDT) -> -420. Western zones are negative.
    """
    aware = datetime.combine(dt.date(), dt.time(), tzinfo=ZoneInfo(clinic_tz))
    off = aware.utcoffset()
    assert off is not None  # zoneinfo always yields an offset
    return int(off // timedelta(minutes=1))


def _clinic_tz_map(db: Session) -> dict:
    """clinic_id -> IANA tz name (defaulting to America/Edmonton)."""
    return {c.id: (c.timezone or DEFAULT_TZ) for c in db.query(Clinic).all()}


def _shift(ts: Optional[datetime], off: int) -> Optional[datetime]:
    """Convert a stored naive-clinic-local value to naive UTC.

    The stored value is clinic-local; UTC = local - offset. Since western
    offsets are negative, `ts - timedelta(minutes=off)` moves the time forward
    (e.g. 14:00 with off=-360 -> 20:00)."""
    if ts is None:
        return None
    return ts - timedelta(minutes=off)


def _candidate_query(db: Session):
    return db.query(Appointment).filter(
        Appointment.source.in_(["booking-web-hold"]) | Appointment.source.is_(None)
    )


def compute_backfill_diffs(db: Session) -> List[BackfillDiff]:
    """Build the in-memory before/after diff for every candidate row.

    Each row is shifted by ITS OWN clinic offset on ITS OWN date. Protected
    (`voice-hold`) rows are excluded by construction.
    """
    tz_map = _clinic_tz_map(db)
    diffs: List[BackfillDiff] = []
    for a in _candidate_query(db).all():
        tz = tz_map.get(a.clinic_id, DEFAULT_TZ)
        off = offset_minutes(tz, a.start_time)
        diffs.append(BackfillDiff(
            appointment_id=a.id,
            source=a.source,
            clinic_tz=tz,
            offset_minutes=off,
            start_before=a.start_time,
            start_after=_shift(a.start_time, off),
            end_before=a.end_time,
            end_after=_shift(a.end_time, off),
        ))
    return diffs


def count_protected(db: Session) -> int:
    return (
        db.query(Appointment)
        .filter(Appointment.source.in_(list(PROTECTED_SOURCES)))
        .count()
    )


def apply_backfill(db: Session, diffs: List[BackfillDiff]) -> None:
    """Apply the computed shift inside a single transaction.

    Guards: the protected (`voice-hold`) row count must be unchanged after the
    update — a tripwire against any accidental scope error.
    """
    protected_before = count_protected(db)
    by_id = {d.appointment_id: d for d in diffs}
    rows = (
        db.query(Appointment)
        .filter(Appointment.id.in_(list(by_id.keys())))
        .all()
        if by_id else []
    )
    for a in rows:
        d = by_id[a.id]
        assert a.source not in PROTECTED_SOURCES, (
            f"refusing to shift protected row {a.id} (source={a.source})"
        )
        a.start_time = d.start_after
        a.end_time = d.end_after
    db.commit()
    assert count_protected(db) == protected_before, (
        "protected voice-hold count changed during backfill — aborting"
    )


def _print_summary(diffs: List[BackfillDiff], protected: int) -> None:
    per_source: dict = {}
    for d in diffs:
        per_source[d.source] = per_source.get(d.source, 0) + 1
    print("=== appointment TZ backfill ===")
    print(f"candidate rows: {len(diffs)}")
    for src, n in sorted(per_source.items(), key=lambda kv: str(kv[0])):
        print(f"  source={src!r}: {n}")
    print(f"protected (voice-hold) rows to SKIP: {protected}")
    print("sample (up to 10):")
    for d in diffs[:10]:
        print(
            f"  {d.appointment_id} [{d.source!r} {d.clinic_tz} off={d.offset_minutes}] "
            f"{d.start_before} -> {d.start_after}"
        )


def main(argv: Optional[list] = None) -> None:  # pragma: no cover - CLI wrapper
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="apply the shift (default is a read-only dry run)")
    args = ap.parse_args(argv)

    from database.connection import SessionLocal

    db = SessionLocal()
    try:
        diffs = compute_backfill_diffs(db)
        protected = count_protected(db)
        _print_summary(diffs, protected)
        if not args.apply:
            print("DRY RUN — no writes. Re-run with --apply after human review.")
            return
        apply_backfill(db, diffs)
        print(f"APPLIED — shifted {len(diffs)} row(s); protected rows unchanged.")
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    main()

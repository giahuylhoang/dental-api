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

One-shot operation
------------------
This is a ONE-SHOT operation. The `--before-created-at` cutoff (set to the
deploy timestamp of the fixed write path for the real run) prevents touching
rows created AFTER the fix, which are already correct UTC. BUT: re-running
`--apply` with the SAME cutoff WILL double-shift the same pre-cutoff rows —
DO NOT re-run it. The printed audit log is the durable record of what was
shifted.

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


def _candidate_query(db: Session, before: Optional[datetime] = None):
    q = db.query(Appointment).filter(
        Appointment.source.in_(["booking-web-hold"]) | Appointment.source.is_(None)
    )
    if before is not None:
        q = q.filter(Appointment.created_at < before)
    return q


def compute_backfill_diffs(
    db: Session, before: Optional[datetime] = None
) -> List[BackfillDiff]:
    """Build the in-memory before/after diff for every candidate row.

    Each row is shifted by ITS OWN clinic offset on ITS OWN date. Protected
    (`voice-hold`) rows are excluded by construction. When ``before`` is given,
    only rows with ``created_at < before`` are considered (so post-fix rows,
    which are already correct UTC, are never touched).
    """
    tz_map = _clinic_tz_map(db)
    diffs: List[BackfillDiff] = []
    for a in _candidate_query(db, before=before).all():
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


def _snapshot_protected(db: Session) -> dict:
    """Snapshot every protected row's (start_time, end_time) keyed by id, for
    a byte-level tamper check after the commit."""
    snap = {}
    for a in (
        db.query(Appointment)
        .filter(Appointment.source.in_(list(PROTECTED_SOURCES)))
        .with_entities(Appointment.id, Appointment.start_time, Appointment.end_time)
        .all()
    ):
        snap[a.id] = (a.start_time, a.end_time)
    return snap


def _verify_protected_unchanged(db: Session, snapshot: dict) -> None:
    """Re-read protected rows and raise RuntimeError if ANY (start, end) pair
    differs from the pre-write snapshot — not just the count (a swap that
    preserves count is still caught)."""
    current = _snapshot_protected(db)
    changed = []
    for aid, pair in snapshot.items():
        if current.get(aid) != pair:
            changed.append(aid)
    # Also catch a protected row vanishing or a new one appearing.
    if set(current) != set(snapshot):
        for aid in set(current) ^ set(snapshot):
            changed.append(aid)
    if changed:
        raise RuntimeError(
            "protected (voice-hold) rows changed during backfill — aborting. "
            f"changed ids: {sorted(changed)}"
        )


def apply_backfill(
    db: Session,
    diffs: List[BackfillDiff],
    before: Optional[datetime] = None,
) -> None:
    """Apply the computed shift inside a single transaction.

    Guards (all raise RuntimeError, never ``assert`` — so ``python -O`` cannot
    strip them):
      1. No diff may target a row whose CURRENT source is protected (defensive
         against a source flip between diff and apply).
      2. Every protected (``voice-hold``) row's (start_time, end_time) must be
         byte-identical before and after the commit — a count-only check would
         miss a timestamp swap.
    """
    by_id = {d.appointment_id: d for d in diffs}
    rows = (
        db.query(Appointment)
        .filter(Appointment.id.in_(list(by_id.keys())))
        .all()
        if by_id else []
    )

    # Defensive: refuse any diff that currently points at a protected row.
    for a in rows:
        if a.source in PROTECTED_SOURCES:
            raise RuntimeError(
                f"refusing to shift protected row {a.id} (source={a.source})"
            )

    protected_snapshot = _snapshot_protected(db)

    for a in rows:
        d = by_id[a.id]
        a.start_time = d.start_after
        a.end_time = d.end_after

    db.commit()

    _verify_protected_unchanged(db, protected_snapshot)

    # Audit: machine-greppable per-row record.
    cutoff_str = before.isoformat() if before else "<none — unbounded>"
    print(f"=== audit: shifted {len(rows)} row(s); cutoff={cutoff_str} ===")
    for a in rows:
        d = by_id[a.id]
        print(
            f"  SHIFT id={a.id} start {d.start_before} -> {d.start_after}"
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


def _parse_iso8601(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--before-created-at must be ISO8601, got {value!r}"
        )


def main(argv: Optional[list] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="apply the shift (default is a read-only dry run)")
    ap.add_argument(
        "--before-created-at",
        type=_parse_iso8601,
        default=None,
        metavar="ISO8601",
        help=(
            "only shift rows with created_at < this cutoff (set to the deploy "
            "timestamp for the real run). REQUIRED for --apply."
        ),
    )
    args = ap.parse_args(argv)

    # --apply requires a cutoff: without it, post-fix rows (already UTC) or a
    # re-run would double-shift. Dry-run without a cutoff is allowed but warned.
    if args.apply and args.before_created_at is None:
        print(
            "ERROR: --apply requires --before-created-at <ISO8601> "
            "(the deploy timestamp of the fixed write path). Without it, "
            "post-fix rows would be double-shifted. Aborting.",
            flush=True,
        )
        raise SystemExit(2)

    from database.connection import SessionLocal

    db = SessionLocal()
    try:
        if args.before_created_at is None and not args.apply:
            print(
                "WARNING: no --before-created-at given — the candidate window is "
                "UNBOUNDED. --apply would be refused. Inspect only.",
                flush=True,
            )
        diffs = compute_backfill_diffs(db, before=args.before_created_at)
        protected = count_protected(db)
        _print_summary(diffs, protected)
        if not args.apply:
            print("DRY RUN — no writes. Re-run with --apply after human review.")
            return
        apply_backfill(db, diffs, before=args.before_created_at)
        print(f"APPLIED — shifted {len(diffs)} row(s); protected rows unchanged.")
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    main()

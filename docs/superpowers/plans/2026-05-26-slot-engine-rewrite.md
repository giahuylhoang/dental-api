# Slot Engine Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken 296-line `tools/slot_utils.py` with a layered `services/slot_engine/` package that consults all 6 schema sources (`clinic_operating_hours`, `clinic_closures`, `provider_availability`, `provider_busy_blocks`, `provider_time_off`, `appointments`), plus ship the missing alembic migration for `provider_busy_blocks` columns.

**Architecture:** Pure-helper composition: `intervals.IntervalSet` primitive → `windows.{clinic_day_window,provider_day_window}` build per-day windows → `subtract.{busy_blocks_for,time_off_for,appointments_for}` carve out unavailable time → `chunk.into_slots` emits slot starts. Orchestrator in `engine.py` loops dates × providers and composes. `tools/slot_utils.py` becomes a 3-line re-export shim (deleted in a follow-up release).

**Tech Stack:** Python 3.11, SQLAlchemy 2.x, alembic, pytz, FastAPI (for the calling endpoint), pytest. Postgres 15 in prod; SQLite for tests.

**Source spec:** `docs/superpowers/specs/2026-05-26-slot-engine-rewrite-design.md`

---

## File Structure

| Path | Status | Responsibility |
|---|---|---|
| `alembic/versions/h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py` | create | Add `weekdays`, `specific_date`, `recurrence_until`, `label` to `provider_busy_blocks`; drop NOT NULL on `weekday`; partial index on `specific_date`. Postgres-only; SQLite path no-ops. |
| `services/slot_engine/__init__.py` | create | Re-export `get_available_slots`, `find_busy_block_overlap`. |
| `services/slot_engine/intervals.py` | create | `IntervalSet` primitive with `from_window`, `subtract`, `intersect`, `is_empty`, `intervals`. Pure (no DB). |
| `services/slot_engine/windows.py` | create | `clinic_day_window`, `provider_day_window`. DB-backed; tz-aware. |
| `services/slot_engine/subtract.py` | create | `busy_blocks_for`, `time_off_for`, `appointments_for`. DB-backed; tz-aware. |
| `services/slot_engine/chunk.py` | create | `into_slots(interval_set, slot_minutes) -> list[datetime]`. Pure. |
| `services/slot_engine/engine.py` | create | Orchestrator `get_available_slots` + `find_busy_block_overlap` + `resolve_providers`. |
| `tools/slot_utils.py` | rewrite | 3-line shim re-exporting from `services.slot_engine`. |
| `tests/services/__init__.py` | create | Empty. |
| `tests/services/test_slot_engine/__init__.py` | create | Empty. |
| `tests/services/test_slot_engine/test_intervals.py` | create | Unit tests for `IntervalSet`. |
| `tests/services/test_slot_engine/test_clinic_day_window.py` | create | Unit tests for `clinic_day_window`. |
| `tests/services/test_slot_engine/test_provider_day_window.py` | create | Unit tests for `provider_day_window`. |
| `tests/services/test_slot_engine/test_busy_blocks_for.py` | create | Unit tests for `busy_blocks_for`. |
| `tests/services/test_slot_engine/test_time_off_for.py` | create | Unit tests for `time_off_for`. |
| `tests/services/test_slot_engine/test_appointments_for.py` | create | Unit tests for `appointments_for`. |
| `tests/services/test_slot_engine/test_chunk_into_slots.py` | create | Unit tests for `chunk.into_slots`. |
| `tests/services/test_slot_engine/test_resolve_providers.py` | create | Unit tests for `engine.resolve_providers`. |
| `tests/test_slot_engine_integration.py` | create | End-to-end scenarios from the Market Mall schedule. |
| `tests/test_busy_block_enforcement.py` | delete | Tests the old algorithm's internals. Replaced by per-helper + integration tests. |

---

## Task 1: Alembic migration for missing `provider_busy_blocks` columns

**Files:**
- Create: `alembic/versions/h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py`

- [ ] **Step 1: Verify current alembic head**

Run:
```bash
cd dental-api
uv run alembic heads
```
Expected: `g1h2i3j4k5l6 (head)`

- [ ] **Step 2: Create the migration file**

Create `alembic/versions/h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py`:

```python
"""provider_busy_blocks v2 columns: weekdays, specific_date, recurrence_until, label

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-26 22:00:00.000000

The model (database/models.py::ProviderBusyBlock) already references these
columns but no prior migration creates them. Production was patched manually
via raw ALTER TABLE during diagnosis; this migration is idempotent against
that patch (ADD COLUMN IF NOT EXISTS) and brings the schema definition
under alembic's tracking.

Postgres-only. SQLite test conftest creates the full schema via models, so
no SQLite path is needed.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return  # SQLite path is no-op; models create the columns directly.

    # Idempotent against prior raw-SQL patch on prod AND fresh DBs.
    # ADD COLUMN IF NOT EXISTS is Postgres 9.6+; we're on 15.
    op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday DROP NOT NULL")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS weekdays VARCHAR")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS specific_date DATE")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS recurrence_until DATE")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS label VARCHAR")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_provider_busy_blocks_specific_date "
        "ON provider_busy_blocks (clinic_id, provider_id, specific_date) "
        "WHERE specific_date IS NOT NULL"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_provider_busy_blocks_specific_date")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS label")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS recurrence_until")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS specific_date")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS weekdays")
    op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday SET NOT NULL")
```

- [ ] **Step 3: Verify alembic recognizes the new head**

Run:
```bash
uv run alembic heads
```
Expected: `h2i3j4k5l6m7 (head)`

Run:
```bash
uv run alembic history -r g1h2i3j4k5l6:h2i3j4k5l6m7
```
Expected: shows the chain `g1h2i3j4k5l6 -> h2i3j4k5l6m7`.

- [ ] **Step 4: Round-trip test against SQLite (no-op should succeed)**

Run:
```bash
uv run pytest tests/test_schema.py -v
```
Expected: PASS. The SQLite schema test re-creates from models and round-trips migrations.

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py
git commit -m "feat(alembic): add provider_busy_blocks v2 columns migration"
```

---

## Task 2: `IntervalSet` primitive + `types.py`

**Files:**
- Create: `services/slot_engine/__init__.py`
- Create: `services/slot_engine/intervals.py`
- Create: `services/slot_engine/types.py`
- Create: `tests/services/__init__.py`
- Create: `tests/services/test_slot_engine/__init__.py`
- Create: `tests/services/test_slot_engine/test_intervals.py`

- [ ] **Step 1: Create empty package init files**

```bash
mkdir -p services/slot_engine
mkdir -p tests/services/test_slot_engine
touch services/slot_engine/__init__.py
touch tests/services/__init__.py
touch tests/services/test_slot_engine/__init__.py
```

- [ ] **Step 2: Write the failing test for `IntervalSet`**

Create `tests/services/test_slot_engine/test_intervals.py`:

```python
"""Unit tests for IntervalSet primitive."""
from datetime import datetime, timedelta, timezone

import pytest

from services.slot_engine.intervals import IntervalSet


TZ = timezone(timedelta(hours=-6))  # MDT


def dt(h, m=0, day=27):
    return datetime(2026, 5, day, h, m, tzinfo=TZ)


def test_from_window_simple():
    s = IntervalSet.from_window(dt(9), dt(17))
    assert s.intervals == [(dt(9), dt(17))]
    assert not s.is_empty


def test_from_window_zero_width_returns_empty():
    s = IntervalSet.from_window(dt(9), dt(9))
    assert s.is_empty
    assert s.intervals == []


def test_from_window_inverted_returns_empty():
    s = IntervalSet.from_window(dt(17), dt(9))
    assert s.is_empty


def test_subtract_carves_middle_into_two_pieces():
    day = IntervalSet.from_window(dt(9), dt(17))
    lunch = IntervalSet.from_window(dt(12), dt(13))
    result = day.subtract(lunch)
    assert result.intervals == [(dt(9), dt(12)), (dt(13), dt(17))]


def test_subtract_at_start_clips_left():
    day = IntervalSet.from_window(dt(9), dt(17))
    morning_block = IntervalSet.from_window(dt(9), dt(11))
    assert day.subtract(morning_block).intervals == [(dt(11), dt(17))]


def test_subtract_at_end_clips_right():
    day = IntervalSet.from_window(dt(9), dt(17))
    afternoon_block = IntervalSet.from_window(dt(15), dt(17))
    assert day.subtract(afternoon_block).intervals == [(dt(9), dt(15))]


def test_subtract_fully_contained_removes_interval():
    day = IntervalSet.from_window(dt(9), dt(17))
    full = IntervalSet.from_window(dt(8), dt(18))
    assert day.subtract(full).is_empty


def test_subtract_non_overlapping_returns_unchanged():
    day = IntervalSet.from_window(dt(9), dt(17))
    evening = IntervalSet.from_window(dt(18), dt(20))
    assert day.subtract(evening).intervals == [(dt(9), dt(17))]


def test_subtract_edge_touching_is_no_op():
    # [9, 12) and [12, 13) touch at 12 — should not subtract anything.
    day = IntervalSet.from_window(dt(9), dt(12))
    touch = IntervalSet.from_window(dt(12), dt(13))
    assert day.subtract(touch).intervals == [(dt(9), dt(12))]


def test_intersect_overlapping():
    a = IntervalSet.from_window(dt(9), dt(15))
    b = IntervalSet.from_window(dt(12), dt(17))
    assert a.intersect(b).intervals == [(dt(12), dt(15))]


def test_intersect_non_overlapping_returns_empty():
    a = IntervalSet.from_window(dt(9), dt(12))
    b = IntervalSet.from_window(dt(13), dt(17))
    assert a.intersect(b).is_empty


def test_intersect_with_empty_returns_empty():
    a = IntervalSet.from_window(dt(9), dt(17))
    e = IntervalSet([])
    assert a.intersect(e).is_empty


def test_subtract_multiple_blocks_in_one_window():
    day = IntervalSet.from_window(dt(9), dt(17))
    blocks = IntervalSet([(dt(10), dt(11)), (dt(14), dt(15))])
    result = day.subtract(blocks)
    assert result.intervals == [
        (dt(9), dt(10)), (dt(11), dt(14)), (dt(15), dt(17)),
    ]


def test_intersect_with_multi_interval_set():
    morning_afternoon = IntervalSet([(dt(9), dt(12)), (dt(13), dt(17))])  # lunch carved
    window = IntervalSet.from_window(dt(11), dt(14))
    assert morning_afternoon.intersect(window).intervals == [
        (dt(11), dt(12)), (dt(13), dt(14)),
    ]
```

- [ ] **Step 3: Run tests to verify they fail with import error**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_intervals.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'services.slot_engine.intervals'`

- [ ] **Step 4: Implement `IntervalSet`**

Create `services/slot_engine/intervals.py`:

```python
"""IntervalSet — pure interval-arithmetic primitive used by the slot engine.

All intervals are half-open [start, end) and timezone-aware. Empty sets are
valid. Methods do not mutate; they return new IntervalSet instances.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


Interval = Tuple[datetime, datetime]


@dataclass(frozen=True)
class IntervalSet:
    """A sorted, non-overlapping set of half-open [start, end) intervals."""

    intervals: List[Interval] = field(default_factory=list)

    @classmethod
    def from_window(cls, start: datetime, end: datetime) -> "IntervalSet":
        """Build a one-interval set; empty if start >= end."""
        if start >= end:
            return cls([])
        return cls([(start, end)])

    @property
    def is_empty(self) -> bool:
        return not self.intervals

    def subtract(self, other: "IntervalSet") -> "IntervalSet":
        """Return self minus other (set difference)."""
        if not other.intervals:
            return IntervalSet(list(self.intervals))
        result: List[Interval] = []
        for s, e in self.intervals:
            pieces = [(s, e)]
            for bs, be in other.intervals:
                next_pieces: List[Interval] = []
                for ps, pe in pieces:
                    # Half-open semantics: [ps,pe) and [bs,be) overlap iff ps<be and bs<pe
                    if pe <= bs or be <= ps:
                        next_pieces.append((ps, pe))
                        continue
                    if ps < bs:
                        next_pieces.append((ps, bs))
                    if be < pe:
                        next_pieces.append((be, pe))
                pieces = next_pieces
                if not pieces:
                    break
            result.extend(pieces)
        return IntervalSet(result)

    def intersect(self, other: "IntervalSet") -> "IntervalSet":
        """Return self ∩ other."""
        if not self.intervals or not other.intervals:
            return IntervalSet([])
        result: List[Interval] = []
        for s, e in self.intervals:
            for bs, be in other.intervals:
                lo = max(s, bs)
                hi = min(e, be)
                if lo < hi:
                    result.append((lo, hi))
        # Result is naturally sorted because both inputs are sorted.
        return IntervalSet(result)
```

Create `services/slot_engine/types.py` (small dataclasses used by the orchestrator):

```python
"""Shared dataclasses for the slot engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class ProviderSlots:
    provider_id: int
    title: Optional[str]
    slots: List[datetime]


@dataclass(frozen=True)
class EngineRequest:
    clinic_id: str
    start_datetime: datetime
    end_datetime: datetime
    slot_minutes: int
    provider_id: Optional[int]
    provider_name: Optional[str]
```

Update `services/slot_engine/__init__.py` (will be filled in later tasks, but add a stub now):

```python
"""Slot engine package. Public re-exports populated as helpers land."""
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_intervals.py -v
```
Expected: PASS (14 tests).

- [ ] **Step 6: Commit**

```bash
git add services/slot_engine/__init__.py services/slot_engine/intervals.py services/slot_engine/types.py
git add tests/services/__init__.py tests/services/test_slot_engine/__init__.py
git add tests/services/test_slot_engine/test_intervals.py
git commit -m "feat(slot_engine): IntervalSet primitive + types"
```

---

## Task 3: `clinic_day_window`

**Files:**
- Create: `services/slot_engine/windows.py`
- Create: `tests/services/test_slot_engine/test_clinic_day_window.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_clinic_day_window.py`:

```python
"""Unit tests for windows.clinic_day_window."""
from datetime import date, datetime, time, timedelta
import logging

import pytest
import pytz

from database.models import Clinic, DEFAULT_CLINIC_ID
from database.v1_1.models import ClinicOperatingHours, ClinicClosure
from services.slot_engine.windows import clinic_day_window


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)   # Monday
SAT = date(2026, 5, 23)   # Saturday


@pytest.fixture
def clinic(db_session):
    c = Clinic(id="test-clinic", name="Test Clinic", timezone="America/Edmonton")
    db_session.add(c)
    db_session.commit()
    return c


def _hours(clinic_id, dow, open_at, close_at, lunch_start=None, lunch_end=None, closed=False):
    return ClinicOperatingHours(
        clinic_id=clinic_id, day_of_week=dow,
        open_at=open_at, close_at=close_at,
        lunch_start=lunch_start, lunch_end=lunch_end, is_closed=closed,
    )


def test_returns_single_interval_when_no_lunch(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 1
    start, end = result.intervals[0]
    assert start == TZ.localize(datetime(2026, 5, 25, 9, 0))
    assert end == TZ.localize(datetime(2026, 5, 25, 17, 0))


def test_carves_lunch_when_both_columns_set(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0),
                          lunch_start=time(12, 0), lunch_end=time(13, 0)))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 2
    assert result.intervals[0] == (
        TZ.localize(datetime(2026, 5, 25, 9, 0)),
        TZ.localize(datetime(2026, 5, 25, 12, 0)),
    )
    assert result.intervals[1] == (
        TZ.localize(datetime(2026, 5, 25, 13, 0)),
        TZ.localize(datetime(2026, 5, 25, 17, 0)),
    )


def test_ignores_lunch_when_only_one_column_set(db_session, clinic, caplog):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0),
                          lunch_start=time(12, 0), lunch_end=None))
    db_session.commit()
    caplog.set_level(logging.WARNING)
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 1  # no lunch carved
    assert "malformed lunch" in caplog.text.lower()


def test_returns_empty_when_no_operating_hours_row(db_session, clinic, caplog):
    # No ClinicOperatingHours rows for this weekday.
    caplog.set_level(logging.WARNING)
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert result.is_empty
    assert "no clinic_operating_hours" in caplog.text.lower()


def test_returns_empty_when_is_closed_true(db_session, clinic):
    db_session.add(_hours(clinic.id, 5, time(0, 0), time(0, 0), closed=True))
    db_session.commit()
    result = clinic_day_window(clinic.id, SAT, db_session, TZ)
    assert result.is_empty


def test_clinic_closure_overrides_operating_hours(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))
    db_session.add(ClinicClosure(
        clinic_id=clinic.id, start_date=MON, end_date=MON,
        kind="holiday", reason="Victoria Day",
    ))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert result.is_empty


def test_multi_day_closure_covers_all_days(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))  # Mon
    db_session.add(_hours(clinic.id, 1, time(9, 0), time(17, 0)))  # Tue
    db_session.add(ClinicClosure(
        clinic_id=clinic.id,
        start_date=date(2026, 5, 25), end_date=date(2026, 5, 26),
        kind="training", reason="staff training",
    ))
    db_session.commit()
    assert clinic_day_window(clinic.id, date(2026, 5, 25), db_session, TZ).is_empty
    assert clinic_day_window(clinic.id, date(2026, 5, 26), db_session, TZ).is_empty
    # Wednesday outside the closure range is still open (need hours row).
    db_session.add(_hours(clinic.id, 2, time(9, 0), time(17, 0)))
    db_session.commit()
    assert not clinic_day_window(clinic.id, date(2026, 5, 27), db_session, TZ).is_empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_clinic_day_window.py -v
```
Expected: FAIL with `ImportError: cannot import name 'clinic_day_window' from 'services.slot_engine.windows'`

- [ ] **Step 3: Implement `clinic_day_window`**

Create `services/slot_engine/windows.py`:

```python
"""Window builders: clinic day window (operating hours + closures + lunch)
and provider day window (narrowed by per-provider availability)."""
from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Set, Tuple

import pytz
from sqlalchemy.orm import Session

from database.models import ProviderAvailability
from database.v1_1.models import ClinicClosure, ClinicOperatingHours
from services.slot_engine.intervals import IntervalSet


logger = logging.getLogger("slot_engine.windows")

# Dedupe per-process: each (clinic_id, day_of_week) warning fires at most once.
_warned_missing_hours: Set[Tuple[str, int]] = set()
_warned_malformed_lunch: Set[Tuple[str, int]] = set()


def _combine(d: date, t: time, tz: pytz.tzinfo.BaseTzInfo) -> datetime:
    """Build a tz-aware datetime from a naive (date, time) pair."""
    return tz.localize(datetime.combine(d, t))


def clinic_day_window(
    clinic_id: str, target_date: date, db: Session, tz: pytz.tzinfo.BaseTzInfo
) -> IntervalSet:
    """Return the intervals when the clinic is potentially open on target_date.

    Decision matrix (see spec 2026-05-26-slot-engine-rewrite-design.md):
      - clinic_closures overlapping target_date -> empty
      - no clinic_operating_hours row for the weekday -> empty (fail closed) + WARN
      - is_closed=True -> empty
      - lunch_start + lunch_end both set -> carve [lunch_start, lunch_end)
      - only one of lunch_* set -> ignore lunch + WARN (malformed config)
    """
    # 1. Closures take precedence.
    closure = (
        db.query(ClinicClosure)
        .filter(
            ClinicClosure.clinic_id == clinic_id,
            ClinicClosure.start_date <= target_date,
        )
        .all()
    )
    for c in closure:
        end = c.end_date if c.end_date is not None else c.start_date
        if c.start_date <= target_date <= end:
            return IntervalSet([])

    # 2. Look up the per-weekday hours.
    dow = target_date.weekday()
    row = (
        db.query(ClinicOperatingHours)
        .filter(
            ClinicOperatingHours.clinic_id == clinic_id,
            ClinicOperatingHours.day_of_week == dow,
        )
        .one_or_none()
    )
    if row is None:
        key = (clinic_id, dow)
        if key not in _warned_missing_hours:
            _warned_missing_hours.add(key)
            logger.warning(
                "No clinic_operating_hours row for clinic=%s dow=%s; treating as closed.",
                clinic_id, dow,
            )
        return IntervalSet([])

    if row.is_closed:
        return IntervalSet([])

    # 3. Build the day window.
    window = IntervalSet.from_window(
        _combine(target_date, row.open_at, tz),
        _combine(target_date, row.close_at, tz),
    )

    # 4. Carve out lunch if both columns set; warn on one-sided config.
    has_lunch_start = row.lunch_start is not None
    has_lunch_end = row.lunch_end is not None
    if has_lunch_start and has_lunch_end:
        lunch = IntervalSet.from_window(
            _combine(target_date, row.lunch_start, tz),
            _combine(target_date, row.lunch_end, tz),
        )
        window = window.subtract(lunch)
    elif has_lunch_start != has_lunch_end:
        key = (clinic_id, dow)
        if key not in _warned_malformed_lunch:
            _warned_malformed_lunch.add(key)
            logger.warning(
                "Malformed lunch config for clinic=%s dow=%s (only one of "
                "lunch_start/lunch_end set); ignoring lunch.",
                clinic_id, dow,
            )

    return window
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_clinic_day_window.py -v
```
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/windows.py tests/services/test_slot_engine/test_clinic_day_window.py
git commit -m "feat(slot_engine): clinic_day_window with lunch + closures + fail-closed missing config"
```

---

## Task 4: `provider_day_window`

**Files:**
- Modify: `services/slot_engine/windows.py` (append `provider_day_window`)
- Create: `tests/services/test_slot_engine/test_provider_day_window.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_provider_day_window.py`:

```python
"""Unit tests for windows.provider_day_window."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider, ProviderAvailability
from services.slot_engine.intervals import IntervalSet
from services.slot_engine.windows import provider_day_window


TZ = pytz.timezone("America/Edmonton")
WED = date(2026, 5, 27)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def _daily():
    """Clinic open Wed 9–17."""
    return IntervalSet.from_window(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 17, 0)),
    )


def test_no_availability_rows_returns_daily_window_unchanged(db_session, setup):
    _, p = setup
    daily = _daily()
    result = provider_day_window(p.id, "c1", WED, daily, db_session, TZ)
    assert result.intervals == daily.intervals


def test_availability_narrows_to_provider_window(db_session, setup):
    _, p = setup
    # Soheil Wed: 9–12 only (half day)
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=9, start_minute=0, end_hour=12, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 12, 0)),
    )]


def test_split_shift_unions_multiple_rows(db_session, setup):
    _, p = setup
    # Two windows same weekday: 9–11 and 14–17.
    db_session.add_all([
        ProviderAvailability(clinic_id="c1", provider_id=p.id, weekday=2,
                             start_hour=9, start_minute=0, end_hour=11, end_minute=0),
        ProviderAvailability(clinic_id="c1", provider_id=p.id, weekday=2,
                             start_hour=14, start_minute=0, end_hour=17, end_minute=0),
    ])
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    assert result.intervals == [
        (TZ.localize(datetime(2026, 5, 27, 9, 0)),  TZ.localize(datetime(2026, 5, 27, 11, 0))),
        (TZ.localize(datetime(2026, 5, 27, 14, 0)), TZ.localize(datetime(2026, 5, 27, 17, 0))),
    ]


def test_availability_extending_past_clinic_hours_is_clipped(db_session, setup):
    _, p = setup
    # Provider says 8–19, clinic only open 9–17.
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=8, start_minute=0, end_hour=19, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    # Clipped to clinic window.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 17, 0)),
    )]


def test_empty_daily_window_returns_empty(db_session, setup):
    _, p = setup
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=9, start_minute=0, end_hour=17, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, IntervalSet([]), db_session, TZ)
    assert result.is_empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_provider_day_window.py -v
```
Expected: FAIL with `ImportError: cannot import name 'provider_day_window' from 'services.slot_engine.windows'`

- [ ] **Step 3: Append `provider_day_window` to `services/slot_engine/windows.py`**

Append to the end of `services/slot_engine/windows.py`:

```python
def provider_day_window(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    daily_window: IntervalSet,
    db: Session,
    tz: pytz.tzinfo.BaseTzInfo,
) -> IntervalSet:
    """Narrow daily_window to a provider's working hours on target_date.

    If the provider has no provider_availability rows for this weekday, return
    daily_window unchanged (decision C: no rows = "available during clinic hours").
    Otherwise union the rows for this weekday and intersect with daily_window.
    """
    if daily_window.is_empty:
        return daily_window

    rows = (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.clinic_id == clinic_id,
            ProviderAvailability.provider_id == provider_id,
            ProviderAvailability.weekday == target_date.weekday(),
        )
        .all()
    )
    if not rows:
        return daily_window

    pieces = []
    for r in rows:
        start = _combine(target_date, time(r.start_hour, r.start_minute), tz)
        end = _combine(target_date, time(r.end_hour, r.end_minute), tz)
        if start < end:
            pieces.append((start, end))
    if not pieces:
        return IntervalSet([])

    # Build a sorted, non-overlapping union. Existing rows may overlap or be
    # out-of-order; flatten via subtract trick (union(A,B) = total - (total - A - B)
    # is overkill — just sort + merge).
    pieces.sort()
    merged = [pieces[0]]
    for s, e in pieces[1:]:
        last_s, last_e = merged[-1]
        if s <= last_e:
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))
    return IntervalSet(merged).intersect(daily_window)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_provider_day_window.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/windows.py tests/services/test_slot_engine/test_provider_day_window.py
git commit -m "feat(slot_engine): provider_day_window with graceful no-rows fallback"
```

---

## Task 5: `subtract.busy_blocks_for`

**Files:**
- Create: `services/slot_engine/subtract.py`
- Create: `tests/services/test_slot_engine/test_busy_blocks_for.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_busy_blocks_for.py`:

```python
"""Unit tests for subtract.busy_blocks_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider, ProviderBusyBlock
from services.slot_engine.subtract import busy_blocks_for


TZ = pytz.timezone("America/Edmonton")
WED = date(2026, 5, 27)  # Wednesday, weekday=2
THU = date(2026, 5, 28)  # Thursday


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def test_no_blocks_returns_empty(db_session, setup):
    _, p = setup
    assert busy_blocks_for(p.id, "c1", WED, TZ, db_session).is_empty


def test_recurring_weekly_block_applies_on_matching_weekday(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[0,2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        label="Lunch",
    ))
    db_session.commit()
    # WED weekday=2 matches
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 12, 0)),
        TZ.localize(datetime(2026, 5, 27, 13, 0)),
    )]
    # THU weekday=3 does NOT match
    assert busy_blocks_for(p.id, "c1", THU, TZ, db_session).is_empty


def test_specific_date_one_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, specific_date=WED,
        start_hour=14, start_minute=0, end_hour=16, end_minute=0,
        label="Dental conference",
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 14, 0)),
        TZ.localize(datetime(2026, 5, 27, 16, 0)),
    )]
    # Other dates unaffected
    assert busy_blocks_for(p.id, "c1", THU, TZ, db_session).is_empty


def test_legacy_weekday_field_treated_as_recurring(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=15, start_minute=0, end_hour=16, end_minute=0,
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 15, 0)),
        TZ.localize(datetime(2026, 5, 27, 16, 0)),
    )]


def test_expired_recurrence_until_does_not_apply(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        recurrence_until=date(2026, 4, 1),  # past
    ))
    db_session.commit()
    assert busy_blocks_for(p.id, "c1", WED, TZ, db_session).is_empty


def test_specific_date_wins_over_weekdays_on_same_day(db_session, setup):
    """Per spec: when both specific_date and weekdays would match on the
    same day, the specific_date row contributes; the recurring row is
    suppressed for that day."""
    _, p = setup
    # Recurring Wed lunch
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        label="Lunch",
    ))
    # One-off block on the same Wed (different time)
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, specific_date=WED,
        start_hour=10, start_minute=0, end_hour=11, end_minute=0,
        label="Conference",
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    # Only the specific_date row contributes.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 10, 0)),
        TZ.localize(datetime(2026, 5, 27, 11, 0)),
    )]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_busy_blocks_for.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'services.slot_engine.subtract'`

- [ ] **Step 3: Implement `busy_blocks_for`**

Create `services/slot_engine/subtract.py`:

```python
"""Subtractive layer: builds IntervalSets of unavailable time from
provider_busy_blocks, provider_time_off, and appointments."""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from typing import List, Tuple

import pytz
from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, ProviderBusyBlock
from database.v1_1.models import ProviderTimeOff
from services.slot_engine.intervals import IntervalSet


_ACTIVE_STATUSES = [
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.PENDING_SYNC,
    AppointmentStatus.PENDING,
]


def _combine(d: date, t: time, tz: pytz.tzinfo.BaseTzInfo) -> datetime:
    return tz.localize(datetime.combine(d, t))


def _block_weekdays(block: ProviderBusyBlock) -> List[int]:
    """Read weekdays from the JSON column, falling back to legacy `weekday` int."""
    if block.weekdays:
        try:
            parsed = json.loads(block.weekdays)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    if block.weekday is not None and block.specific_date is None:
        return [int(block.weekday)]
    return []


def busy_blocks_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return busy intervals from provider_busy_blocks that apply on target_date.

    Decision: when both a specific_date and a weekdays row would match
    target_date, the specific_date row wins (the recurring rule is suppressed
    for that day).
    """
    rows = (
        db.query(ProviderBusyBlock)
        .filter(
            ProviderBusyBlock.clinic_id == clinic_id,
            ProviderBusyBlock.provider_id == provider_id,
        )
        .all()
    )

    specific_pieces: List[Tuple[datetime, datetime]] = []
    recurring_pieces: List[Tuple[datetime, datetime]] = []

    for b in rows:
        if b.specific_date is not None:
            if b.specific_date == target_date:
                specific_pieces.append((
                    _combine(target_date, time(int(b.start_hour), int(b.start_minute)), tz),
                    _combine(target_date, time(int(b.end_hour), int(b.end_minute)), tz),
                ))
            continue
        # Recurring rule
        weekdays = _block_weekdays(b)
        if target_date.weekday() not in weekdays:
            continue
        if b.recurrence_until is not None and b.recurrence_until < target_date:
            continue
        recurring_pieces.append((
            _combine(target_date, time(int(b.start_hour), int(b.start_minute)), tz),
            _combine(target_date, time(int(b.end_hour), int(b.end_minute)), tz),
        ))

    pieces = specific_pieces if specific_pieces else recurring_pieces
    return IntervalSet(sorted(pieces))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_busy_blocks_for.py -v
```
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/subtract.py tests/services/test_slot_engine/test_busy_blocks_for.py
git commit -m "feat(slot_engine): busy_blocks_for with specific_date precedence"
```

---

## Task 6: `subtract.time_off_for`

**Files:**
- Modify: `services/slot_engine/subtract.py` (append)
- Create: `tests/services/test_slot_engine/test_time_off_for.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_time_off_for.py`:

```python
"""Unit tests for subtract.time_off_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider
from database.v1_1.models import ProviderTimeOff
from services.slot_engine.subtract import time_off_for


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)
TUE = date(2026, 5, 26)
WED = date(2026, 5, 27)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Nadeem", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def test_no_time_off_returns_empty(db_session, setup):
    _, p = setup
    assert time_off_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_full_day_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 0, 0)),
        end_at=TZ.localize(datetime(2026, 5, 26, 0, 0)),
        reason="vacation",
    ))
    db_session.commit()
    result = time_off_for(p.id, "c1", MON, TZ, db_session)
    # Whole day Mon covered.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 0, 0)),
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
    )]


def test_partial_afternoon_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 13, 0)),
        end_at=TZ.localize(datetime(2026, 5, 25, 17, 0)),
        reason="admin",
    ))
    db_session.commit()
    result = time_off_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 13, 0)),
        TZ.localize(datetime(2026, 5, 25, 17, 0)),
    )]


def test_multi_day_pto_contributes_on_each_day(db_session, setup):
    _, p = setup
    # Mon morning through Wed end of day
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 10, 0)),
        end_at=TZ.localize(datetime(2026, 5, 27, 18, 0)),
        reason="vacation",
    ))
    db_session.commit()
    # Mon: from 10:00 to end of day
    mon_r = time_off_for(p.id, "c1", MON, TZ, db_session)
    assert mon_r.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
    )]
    # Tue: full day
    tue_r = time_off_for(p.id, "c1", TUE, TZ, db_session)
    assert tue_r.intervals == [(
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
        TZ.localize(datetime(2026, 5, 27, 0, 0)),
    )]
    # Wed: start of day to 18:00
    wed_r = time_off_for(p.id, "c1", WED, TZ, db_session)
    assert wed_r.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 0, 0)),
        TZ.localize(datetime(2026, 5, 27, 18, 0)),
    )]


def test_pto_in_different_week_does_not_apply(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 6, 1, 0, 0)),
        end_at=TZ.localize(datetime(2026, 6, 8, 0, 0)),
        reason="vacation",
    ))
    db_session.commit()
    assert time_off_for(p.id, "c1", MON, TZ, db_session).is_empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_time_off_for.py -v
```
Expected: FAIL with `ImportError: cannot import name 'time_off_for' from 'services.slot_engine.subtract'`

- [ ] **Step 3: Append `time_off_for` to `services/slot_engine/subtract.py`**

Append to the end of `services/slot_engine/subtract.py`:

```python
def time_off_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return the intersection of provider_time_off rows with target_date.

    Multi-day PTO contributes [date 00:00, date 24:00) ∩ [start_at, end_at)
    per overlapping date.
    """
    day_start = _combine(target_date, time(0, 0), tz)
    day_end = day_start + timedelta(days=1)

    rows = (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.clinic_id == clinic_id,
            ProviderTimeOff.provider_id == provider_id,
            ProviderTimeOff.start_at < day_end,
            ProviderTimeOff.end_at > day_start,
        )
        .all()
    )

    pieces = []
    for r in rows:
        start_at = r.start_at if r.start_at.tzinfo else tz.localize(r.start_at)
        end_at = r.end_at if r.end_at.tzinfo else tz.localize(r.end_at)
        lo = max(day_start, start_at)
        hi = min(day_end, end_at)
        if lo < hi:
            pieces.append((lo, hi))
    return IntervalSet(sorted(pieces))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_time_off_for.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/subtract.py tests/services/test_slot_engine/test_time_off_for.py
git commit -m "feat(slot_engine): time_off_for with multi-day clipping"
```

---

## Task 7: `subtract.appointments_for`

**Files:**
- Modify: `services/slot_engine/subtract.py` (append)
- Create: `tests/services/test_slot_engine/test_appointments_for.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_appointments_for.py`:

```python
"""Unit tests for subtract.appointments_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Appointment, AppointmentStatus, Clinic, Provider
from services.slot_engine.subtract import appointments_for


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def _apt(p_id, start, end, status=AppointmentStatus.SCHEDULED):
    return Appointment(
        clinic_id="c1", provider_id=p_id,
        start_time=start, end_time=end, status=status,
        notes="t",
    )


def test_no_appointments_returns_empty(db_session, setup):
    _, p = setup
    assert appointments_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_active_appointment_contributes_interval(db_session, setup):
    _, p = setup
    db_session.add(_apt(
        p.id,
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 25, 11, 0)),
    ))
    db_session.commit()
    result = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 25, 11, 0)),
    )]


def test_cancelled_completed_no_show_excluded(db_session, setup):
    _, p = setup
    for st in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED,
               AppointmentStatus.NO_SHOW):
        db_session.add(_apt(
            p.id,
            TZ.localize(datetime(2026, 5, 25, 10, 0)),
            TZ.localize(datetime(2026, 5, 25, 11, 0)),
            status=st,
        ))
    db_session.commit()
    assert appointments_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_confirmed_pending_pending_sync_all_count_as_busy(db_session, setup):
    _, p = setup
    statuses = [
        (AppointmentStatus.CONFIRMED,   9,  10),
        (AppointmentStatus.PENDING,    10,  11),
        (AppointmentStatus.PENDING_SYNC, 11, 12),
    ]
    for st, sh, eh in statuses:
        db_session.add(_apt(
            p.id,
            TZ.localize(datetime(2026, 5, 25, sh, 0)),
            TZ.localize(datetime(2026, 5, 25, eh, 0)),
            status=st,
        ))
    db_session.commit()
    result = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [
        (TZ.localize(datetime(2026, 5, 25,  9, 0)), TZ.localize(datetime(2026, 5, 25, 10, 0))),
        (TZ.localize(datetime(2026, 5, 25, 10, 0)), TZ.localize(datetime(2026, 5, 25, 11, 0))),
        (TZ.localize(datetime(2026, 5, 25, 11, 0)), TZ.localize(datetime(2026, 5, 25, 12, 0))),
    ]


def test_appointment_crossing_midnight_clips_per_day(db_session, setup):
    _, p = setup
    # 23:00 Mon to 02:00 Tue
    db_session.add(_apt(
        p.id,
        TZ.localize(datetime(2026, 5, 25, 23, 0)),
        TZ.localize(datetime(2026, 5, 26,  2, 0)),
    ))
    db_session.commit()
    mon_r = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert mon_r.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 23, 0)),
        TZ.localize(datetime(2026, 5, 26,  0, 0)),
    )]
    tue_r = appointments_for(p.id, "c1", date(2026, 5, 26), TZ, db_session)
    assert tue_r.intervals == [(
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
        TZ.localize(datetime(2026, 5, 26, 2, 0)),
    )]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_appointments_for.py -v
```
Expected: FAIL with `ImportError: cannot import name 'appointments_for' from 'services.slot_engine.subtract'`

- [ ] **Step 3: Append `appointments_for` to `services/slot_engine/subtract.py`**

Append to the end of `services/slot_engine/subtract.py`:

```python
def appointments_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return busy intervals from active appointments overlapping target_date.

    Active = status in {SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING}.
    Midnight-crossing appointments are clipped to [date 00:00, date 24:00).
    """
    day_start = _combine(target_date, time(0, 0), tz)
    day_end = day_start + timedelta(days=1)

    rows = (
        db.query(Appointment)
        .filter(
            Appointment.clinic_id == clinic_id,
            Appointment.provider_id == provider_id,
            Appointment.status.in_(_ACTIVE_STATUSES),
            Appointment.start_time < day_end,
            Appointment.end_time > day_start,
        )
        .order_by(Appointment.start_time.asc())
        .all()
    )

    pieces = []
    for r in rows:
        st = r.start_time if r.start_time.tzinfo else tz.localize(r.start_time)
        et = r.end_time if r.end_time.tzinfo else tz.localize(r.end_time)
        lo = max(day_start, st)
        hi = min(day_end, et)
        if lo < hi:
            pieces.append((lo, hi))
    return IntervalSet(pieces)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_appointments_for.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/subtract.py tests/services/test_slot_engine/test_appointments_for.py
git commit -m "feat(slot_engine): appointments_for with active-status filter + midnight clipping"
```

---

## Task 8: `chunk.into_slots`

**Files:**
- Create: `services/slot_engine/chunk.py`
- Create: `tests/services/test_slot_engine/test_chunk_into_slots.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_slot_engine/test_chunk_into_slots.py`:

```python
"""Unit tests for chunk.into_slots."""
from datetime import datetime, timedelta, timezone

from services.slot_engine.chunk import into_slots
from services.slot_engine.intervals import IntervalSet


TZ = timezone(timedelta(hours=-6))


def dt(h, m=0):
    return datetime(2026, 5, 27, h, m, tzinfo=TZ)


def test_single_window_30_min_chunks():
    s = IntervalSet.from_window(dt(9), dt(11))
    assert into_slots(s, 30) == [dt(9), dt(9, 30), dt(10), dt(10, 30)]


def test_empty_interval_set_returns_empty():
    assert into_slots(IntervalSet([]), 30) == []


def test_window_smaller_than_slot_returns_empty():
    s = IntervalSet.from_window(dt(9), dt(9, 20))
    assert into_slots(s, 30) == []


def test_non_dividing_window_drops_trailing_partial():
    # 9:00-9:45 with 30-min slots: only 9:00 (since 9:30+30=10:00 > 9:45).
    s = IntervalSet.from_window(dt(9), dt(9, 45))
    assert into_slots(s, 30) == [dt(9)]


def test_multiple_disjoint_intervals_concatenated():
    morning_afternoon = IntervalSet([(dt(9), dt(11)), (dt(13), dt(14, 30))])
    assert into_slots(morning_afternoon, 30) == [
        dt(9), dt(9, 30), dt(10), dt(10, 30),
        dt(13), dt(13, 30), dt(14),
    ]


def test_60_minute_slots():
    s = IntervalSet.from_window(dt(9), dt(13))
    assert into_slots(s, 60) == [dt(9), dt(10), dt(11), dt(12)]


def test_slot_exactly_fits_window():
    # 9:00-9:30 with 30-min slots: one slot at 9:00.
    s = IntervalSet.from_window(dt(9), dt(9, 30))
    assert into_slots(s, 30) == [dt(9)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_chunk_into_slots.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'services.slot_engine.chunk'`

- [ ] **Step 3: Implement `into_slots`**

Create `services/slot_engine/chunk.py`:

```python
"""Chunk an IntervalSet into slot start times of fixed duration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from services.slot_engine.intervals import IntervalSet


def into_slots(interval_set: IntervalSet, slot_minutes: int) -> List[datetime]:
    """For each interval [s, e), emit s, s+Δ, s+2Δ, … while start+Δ ≤ e.

    Returns a flat, sorted list of timezone-aware datetimes. Trailing partial
    slots that don't fit a full slot_minutes are discarded.
    """
    delta = timedelta(minutes=slot_minutes)
    out: List[datetime] = []
    for start, end in interval_set.intervals:
        cursor = start
        while cursor + delta <= end:
            out.append(cursor)
            cursor = cursor + delta
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_chunk_into_slots.py -v
```
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add services/slot_engine/chunk.py tests/services/test_slot_engine/test_chunk_into_slots.py
git commit -m "feat(slot_engine): chunk.into_slots with trailing-partial discard"
```

---

## Task 9: `engine.py` — orchestrator + `resolve_providers` + `find_busy_block_overlap` + integration tests

**Files:**
- Create: `services/slot_engine/engine.py`
- Modify: `services/slot_engine/__init__.py` (export public API)
- Create: `tests/services/test_slot_engine/test_resolve_providers.py`
- Create: `tests/test_slot_engine_integration.py`

- [ ] **Step 1: Write the failing `resolve_providers` test**

Create `tests/services/test_slot_engine/test_resolve_providers.py`:

```python
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
```

- [ ] **Step 2: Run the resolve_providers test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_resolve_providers.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'services.slot_engine.engine'`

- [ ] **Step 3: Implement `engine.py`**

Create `services/slot_engine/engine.py`:

```python
"""Slot engine orchestrator.

Public surface:
  - get_available_slots(...)  — same signature as the legacy tools.slot_utils.
  - find_busy_block_overlap(...) — same signature, called from services/appointments.py.
  - resolve_providers(...) — helper exposed for testability.

Internals:
  Compose clinic_day_window → provider_day_window → subtract busy_blocks_for
  + time_off_for + appointments_for → chunk.into_slots, iterating dates × providers.
"""
from __future__ import annotations

import datetime as _dt
import logging
import warnings
from typing import Any, Dict, List, Optional

import pytz
from sqlalchemy.orm import Session

from database.models import Provider, ProviderBusyBlock
from services.slot_engine.chunk import into_slots
from services.slot_engine.intervals import IntervalSet
from services.slot_engine.subtract import (
    appointments_for,
    busy_blocks_for,
    time_off_for,
)
from services.slot_engine.windows import clinic_day_window, provider_day_window


logger = logging.getLogger("slot_engine.engine")

EDMONTON_TZ = pytz.timezone("America/Edmonton")


def resolve_providers(
    clinic_id: Optional[str],
    provider_id: Optional[int],
    provider_name: Optional[str],
    db: Session,
) -> List[Provider]:
    """Return active providers matching the filters.

    Precedence: provider_id > provider_name > all active.
    """
    q = db.query(Provider).filter(Provider.is_active == True)  # noqa: E712
    if clinic_id:
        q = q.filter(Provider.clinic_id == clinic_id)

    if provider_id is not None:
        match = q.filter(Provider.id == provider_id).first()
        return [match] if match else []
    if provider_name:
        match = q.filter(Provider.name.ilike(f"%{provider_name}%")).first()
        return [match] if match else []
    return q.order_by(Provider.id.asc()).all()


def _parse_dt(s: str, tz: pytz.tzinfo.BaseTzInfo) -> Optional[_dt.datetime]:
    try:
        d = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return tz.localize(d) if d.tzinfo is None else d.astimezone(tz)


def _date_range(start_dt: _dt.datetime, end_dt: _dt.datetime) -> List[_dt.date]:
    days: List[_dt.date] = []
    cursor = start_dt.date()
    last = end_dt.date()
    while cursor <= last:
        days.append(cursor)
        cursor = cursor + _dt.timedelta(days=1)
    return days


def _clinic_tz(db: Session, clinic_id: Optional[str], explicit: Optional[str]) -> pytz.tzinfo.BaseTzInfo:
    if explicit:
        return pytz.timezone(explicit)
    if clinic_id:
        from database.models import Clinic
        c = db.get(Clinic, clinic_id)
        if c and c.timezone:
            return pytz.timezone(c.timezone)
    return EDMONTON_TZ


def get_available_slots(
    db: Session,
    start_datetime: str,
    end_datetime: str,
    provider_id: Optional[int] = None,
    provider_name: Optional[str] = None,
    slot_minutes: int = 30,
    clinic_id: Optional[str] = None,
    timezone_str: Optional[str] = None,
    hour_start: Optional[int] = None,
    hour_end: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute available slots across the request window.

    Output shape preserved from legacy tools.slot_utils:
      - If provider_id or provider_name is given:
          {"provider": {"provider_id": int|None, "title": str|None}, "slots": [iso, ...]}
      - Otherwise:
          {"providers": [{"provider_id": int, "title": str, "slots": [iso, ...]}, ...]}

    `hour_start` / `hour_end` are accepted for backwards-compat but silently
    ignored — the new engine reads from clinic_operating_hours instead.
    """
    if hour_start is not None or hour_end is not None:
        warnings.warn(
            "hour_start/hour_end are deprecated and ignored by the slot engine; "
            "configure clinic_operating_hours instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    tz = _clinic_tz(db, clinic_id, timezone_str)

    start_dt = _parse_dt(start_datetime, tz)
    end_dt = _parse_dt(end_datetime, tz)
    if start_dt is None or end_dt is None or end_dt <= start_dt:
        # Preserve legacy behavior on parse failure: empty providers list.
        if provider_id is not None or provider_name is not None:
            return {"provider": {"provider_id": provider_id, "title": None}, "slots": []}
        return {"providers": []}

    if (end_dt - start_dt).days > 90:
        logger.warning(
            "Slot request spans %d days (clinic=%s); no hard cap.",
            (end_dt - start_dt).days, clinic_id,
        )

    providers = resolve_providers(clinic_id, provider_id, provider_name, db)
    if not providers and (provider_id is not None or provider_name is not None):
        return {"provider": {"provider_id": provider_id, "title": None}, "slots": []}

    request_window = IntervalSet.from_window(start_dt, end_dt)
    results: Dict[int, List[_dt.datetime]] = {p.id: [] for p in providers}

    for d in _date_range(start_dt, end_dt):
        daily = clinic_day_window(clinic_id, d, db, tz) if clinic_id else IntervalSet([])
        if daily.is_empty:
            continue
        for p in providers:
            win = provider_day_window(p.id, clinic_id, d, daily, db, tz)
            win = win.subtract(busy_blocks_for(p.id, clinic_id, d, tz, db))
            win = win.subtract(time_off_for(p.id, clinic_id, d, tz, db))
            win = win.subtract(appointments_for(p.id, clinic_id, d, tz, db))
            win = win.intersect(request_window)
            results[p.id].extend(into_slots(win, slot_minutes))

    if provider_id is not None or provider_name is not None:
        # Single provider response shape.
        p = providers[0] if providers else None
        return {
            "provider": {
                "provider_id": p.id if p else provider_id,
                "title": p.title if p else None,
            },
            "slots": [s.isoformat() for s in results.get(p.id, [])] if p else [],
        }

    return {
        "providers": [
            {
                "provider_id": p.id,
                "title": p.title,
                "slots": [s.isoformat() for s in results[p.id]],
            }
            for p in providers
        ]
    }


def find_busy_block_overlap(
    db: Session,
    clinic_id: str,
    provider_id: int,
    start_dt: _dt.datetime,
    end_dt: _dt.datetime,
    tz: pytz.tzinfo.BaseTzInfo,
) -> Optional[ProviderBusyBlock]:
    """Return the first ProviderBusyBlock that overlaps [start_dt, end_dt).

    Caller (services/appointments.py) uses the returned ORM row to populate
    a 409 error response. Returning None means the window is free of blocks.
    """
    start_dt = start_dt if start_dt.tzinfo else tz.localize(start_dt)
    end_dt = end_dt if end_dt.tzinfo else tz.localize(end_dt)
    request = IntervalSet.from_window(start_dt, end_dt)

    rows = (
        db.query(ProviderBusyBlock)
        .filter(
            ProviderBusyBlock.clinic_id == clinic_id,
            ProviderBusyBlock.provider_id == provider_id,
        )
        .all()
    )
    # Reuse busy_blocks_for per day: walk dates in the request window,
    # and on the first overlapping day return the row that matched.
    cursor = start_dt.date()
    last = end_dt.date()
    while cursor <= last:
        # Re-query per day so the "specific_date wins" precedence applies.
        blocks_intervals = busy_blocks_for(provider_id, clinic_id, cursor, tz, db)
        if not request.intersect(blocks_intervals).is_empty:
            # Find the row corresponding to the first overlapping interval.
            for r in rows:
                # Reconstruct the same intervals busy_blocks_for would emit
                # and check if any overlap the request on this date.
                day_blocks = busy_blocks_for(provider_id, clinic_id, cursor, tz, db)
                # If this row's date applies and overlaps, return it.
                row_applies = (
                    (r.specific_date is not None and r.specific_date == cursor)
                    or (
                        r.specific_date is None
                        and cursor.weekday()
                        in _row_weekdays(r)
                        and (r.recurrence_until is None or r.recurrence_until >= cursor)
                    )
                )
                if not row_applies:
                    continue
                rs = tz.localize(_dt.datetime.combine(
                    cursor, _dt.time(int(r.start_hour), int(r.start_minute))
                ))
                re_ = tz.localize(_dt.datetime.combine(
                    cursor, _dt.time(int(r.end_hour), int(r.end_minute))
                ))
                if not IntervalSet.from_window(rs, re_).intersect(request).is_empty:
                    return r
        cursor = cursor + _dt.timedelta(days=1)
    return None


def _row_weekdays(b: ProviderBusyBlock) -> List[int]:
    """Local copy of subtract._block_weekdays (avoids importing private)."""
    import json as _json
    if b.weekdays:
        try:
            parsed = _json.loads(b.weekdays)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except (_json.JSONDecodeError, ValueError, TypeError):
            pass
    if b.weekday is not None and b.specific_date is None:
        return [int(b.weekday)]
    return []
```

- [ ] **Step 4: Update `services/slot_engine/__init__.py` to export the public API**

Replace `services/slot_engine/__init__.py`:

```python
"""Slot engine package — composable per-day, per-provider availability."""
from services.slot_engine.engine import (
    find_busy_block_overlap,
    get_available_slots,
    resolve_providers,
)

__all__ = ["get_available_slots", "find_busy_block_overlap", "resolve_providers"]
```

- [ ] **Step 5: Run resolve_providers tests to verify they pass**

Run:
```bash
uv run pytest tests/services/test_slot_engine/test_resolve_providers.py -v
```
Expected: PASS (6 tests).

- [ ] **Step 6: Write the integration test**

Create `tests/test_slot_engine_integration.py`:

```python
"""End-to-end integration tests for the slot engine, mirroring the
Market Mall denture clinic schedule from the rewrite spec."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import (
    Appointment, AppointmentStatus,
    Clinic, Provider, ProviderAvailability,
)
from database.v1_1.models import ClinicOperatingHours, ProviderTimeOff
from services.slot_engine import get_available_slots


TZ = pytz.timezone("America/Edmonton")

# 2026-05-25 is a Monday in our test fixture.
MON = "2026-05-25T09:00:00-06:00"
SUN_END = "2026-05-31T23:59:00-06:00"
WED_START = "2026-05-27T09:00:00-06:00"
WED_END = "2026-05-27T18:00:00-06:00"
FRI_START = "2026-05-29T09:00:00-06:00"
FRI_END = "2026-05-29T19:00:00-06:00"


@pytest.fixture
def mm(db_session):
    """Seed Market Mall fixture: clinic + hours + 2 providers + availability."""
    c = Clinic(id="mm", name="Market Mall", timezone="America/Edmonton")
    # Clinic hours: Mon-Thu 9-17, Fri 9-18:30, Sat/Sun closed.
    hours = [
        (0, time(9, 0), time(17, 0), False),
        (1, time(9, 0), time(17, 0), False),
        (2, time(9, 0), time(17, 0), False),
        (3, time(9, 0), time(17, 0), False),
        (4, time(9, 0), time(18, 30), False),
        (5, time(0, 0), time(0, 0), True),
        (6, time(0, 0), time(0, 0), True),
    ]
    for dow, o, cl, closed in hours:
        db_session.add(ClinicOperatingHours(
            clinic_id="mm", day_of_week=dow, open_at=o, close_at=cl, is_closed=closed,
        ))
    soheil = Provider(clinic_id="mm", name="Soheil", title="Denturist", is_active=True)
    nadeem = Provider(clinic_id="mm", name="Nadeem", title="Denturist", is_active=True)
    db_session.add_all([soheil, nadeem])
    db_session.flush()
    # Soheil: Tue 9-17, Wed 9-12, Fri 15-18:30
    db_session.add_all([
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=1,
                             start_hour=9, start_minute=0, end_hour=17, end_minute=0),
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=2,
                             start_hour=9, start_minute=0, end_hour=12, end_minute=0),
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=4,
                             start_hour=15, start_minute=0, end_hour=18, end_minute=30),
    ])
    # Nadeem: Mon-Thu 9-17, Fri 9-12
    for dow in (0, 1, 2, 3):
        db_session.add(ProviderAvailability(
            clinic_id="mm", provider_id=nadeem.id, weekday=dow,
            start_hour=9, start_minute=0, end_hour=17, end_minute=0,
        ))
    db_session.add(ProviderAvailability(
        clinic_id="mm", provider_id=nadeem.id, weekday=4,
        start_hour=9, start_minute=0, end_hour=12, end_minute=0,
    ))
    db_session.commit()
    return {"clinic_id": "mm", "soheil": soheil.id, "nadeem": nadeem.id}


def _slots(result, provider_id):
    """Find slots for a provider in the multi-provider response."""
    for p in result["providers"]:
        if p["provider_id"] == provider_id:
            return p["slots"]
    return []


def test_soheil_monday_returns_no_slots(db_session, mm):
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    mon_slots = [s for s in out["slots"] if s.startswith("2026-05-25")]
    assert mon_slots == []


def test_soheil_wednesday_morning_only(db_session, mm):
    out = get_available_slots(
        db_session, WED_START, WED_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    # 9:00 through 11:30 inclusive = 6 slots (last is 11:30+30=12:00 = end).
    assert out["slots"] == [
        "2026-05-27T09:00:00-06:00",
        "2026-05-27T09:30:00-06:00",
        "2026-05-27T10:00:00-06:00",
        "2026-05-27T10:30:00-06:00",
        "2026-05-27T11:00:00-06:00",
        "2026-05-27T11:30:00-06:00",
    ]


def test_soheil_friday_evening_clipped_to_clinic_close(db_session, mm):
    out = get_available_slots(
        db_session, FRI_START, FRI_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    # Soheil 15:00-18:30, clinic closes 18:30 → 15:00, 15:30, 16:00, 16:30,
    # 17:00, 17:30, 18:00 (18:00+30=18:30 = end, included)
    assert out["slots"] == [
        "2026-05-29T15:00:00-06:00",
        "2026-05-29T15:30:00-06:00",
        "2026-05-29T16:00:00-06:00",
        "2026-05-29T16:30:00-06:00",
        "2026-05-29T17:00:00-06:00",
        "2026-05-29T17:30:00-06:00",
        "2026-05-29T18:00:00-06:00",
    ]


def test_nadeem_friday_morning_only(db_session, mm):
    out = get_available_slots(
        db_session, FRI_START, FRI_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # 9:00 through 11:30 inclusive.
    assert out["slots"] == [
        "2026-05-29T09:00:00-06:00",
        "2026-05-29T09:30:00-06:00",
        "2026-05-29T10:00:00-06:00",
        "2026-05-29T10:30:00-06:00",
        "2026-05-29T11:00:00-06:00",
        "2026-05-29T11:30:00-06:00",
    ]


def test_saturday_and_sunday_return_no_slots_for_any_provider(db_session, mm):
    out = get_available_slots(
        db_session,
        "2026-05-30T00:00:00-06:00", "2026-06-01T00:00:00-06:00",
        slot_minutes=30, clinic_id=mm["clinic_id"],
    )
    for p in out["providers"]:
        assert p["slots"] == []


def test_existing_appointment_carves_out_those_slots(db_session, mm):
    db_session.add(Appointment(
        clinic_id="mm", provider_id=mm["nadeem"],
        start_time=TZ.localize(datetime(2026, 5, 25, 10, 0)),
        end_time=TZ.localize(datetime(2026, 5, 25, 11, 0)),
        status=AppointmentStatus.SCHEDULED, notes="t",
    ))
    db_session.commit()
    out = get_available_slots(
        db_session, MON, "2026-05-25T17:00:00-06:00", slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # 10:00 and 10:30 should be missing.
    assert "2026-05-25T10:00:00-06:00" not in out["slots"]
    assert "2026-05-25T10:30:00-06:00" not in out["slots"]
    # But 11:00 should be present.
    assert "2026-05-25T11:00:00-06:00" in out["slots"]


def test_multi_day_time_off_blocks_all_overlapping_days(db_session, mm):
    db_session.add(ProviderTimeOff(
        clinic_id="mm", provider_id=mm["nadeem"],
        start_at=TZ.localize(datetime(2026, 5, 25, 0, 0)),
        end_at=TZ.localize(datetime(2026, 5, 28, 0, 0)),  # off Mon-Wed inclusive
        reason="vacation",
    ))
    db_session.commit()
    out = get_available_slots(
        db_session, MON, "2026-05-28T17:00:00-06:00", slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # No slots Mon, Tue, Wed.
    for d in ("2026-05-25", "2026-05-26", "2026-05-27"):
        assert not any(s.startswith(d) for s in out["slots"]), f"slots leaked on {d}"
    # Thu slots should be present.
    assert any(s.startswith("2026-05-28") for s in out["slots"])


def test_no_clinic_operating_hours_returns_empty(db_session):
    c = Clinic(id="empty", name="Empty", timezone="America/Edmonton")
    p = Provider(clinic_id="empty", name="X", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30,
        clinic_id="empty", provider_id=p.id,
    )
    assert out["slots"] == []


def test_no_providers_returns_empty_providers_list(db_session):
    c = Clinic(id="noprov", name="No Providers", timezone="America/Edmonton")
    db_session.add(c)
    db_session.commit()
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30, clinic_id="noprov",
    )
    assert out == {"providers": []}
```

- [ ] **Step 7: Run all integration tests**

Run:
```bash
uv run pytest tests/test_slot_engine_integration.py -v
```
Expected: PASS (9 tests).

- [ ] **Step 8: Run the entire slot engine suite as a regression check**

Run:
```bash
uv run pytest tests/services/test_slot_engine/ tests/test_slot_engine_integration.py -v
```
Expected: 64 tests pass (14 intervals + 7 clinic_window + 5 provider_window + 6 busy_blocks + 5 time_off + 5 appointments + 7 chunk + 6 resolve + 9 integration). Adjust if any test count drifted.

- [ ] **Step 9: Commit**

```bash
git add services/slot_engine/__init__.py services/slot_engine/engine.py
git add tests/services/test_slot_engine/test_resolve_providers.py
git add tests/test_slot_engine_integration.py
git commit -m "feat(slot_engine): orchestrator + integration tests for Market Mall schedule"
```

---

## Task 10: Wire the shim, delete the old test, verify end-to-end

**Files:**
- Modify: `tools/slot_utils.py` (rewrite as shim)
- Delete: `tests/test_busy_block_enforcement.py`
- Verify: `tests/portal/test_schedule.py` still passes

- [ ] **Step 1: Replace `tools/slot_utils.py` with a shim**

Replace the entire contents of `tools/slot_utils.py` with:

```python
"""Shim — slot logic moved to services.slot_engine.

This module is kept for one release cycle so callers using
`from tools.slot_utils import get_available_slots / find_busy_block_overlap`
don't need to change immediately. Delete this file once no imports
of `tools.slot_utils` remain in either dental-api or dental-agent.
"""
from services.slot_engine import find_busy_block_overlap, get_available_slots  # noqa: F401

__all__ = ["get_available_slots", "find_busy_block_overlap"]
```

- [ ] **Step 2: Delete the old algorithm-specific test**

```bash
git rm tests/test_busy_block_enforcement.py
```

- [ ] **Step 3: Confirm portal tests still pass (public output shape preserved)**

Run:
```bash
uv run pytest tests/portal/test_schedule.py -v
```
Expected: PASS (counts depend on existing test file; no test should fail).

- [ ] **Step 4: Run the entire test suite as a regression sweep**

Run:
```bash
uv run pytest -x -q
```
Expected: full suite passes. Any failure here indicates a caller of the old `tools.slot_utils` internals that the shim didn't cover — fix and retry.

- [ ] **Step 5: Commit**

```bash
git add tools/slot_utils.py
git commit -m "refactor(slot_utils): shim to services.slot_engine; drop test_busy_block_enforcement (replaced)"
```

- [ ] **Step 6: Deploy via the existing cloudbuild pipeline**

Run:
```bash
SHA=$(git rev-parse --short HEAD)
gcloud builds submit \
  --project=rockyridgeai-dental \
  --region=northamerica-northeast2 \
  --config=cloudbuild.yaml \
  --substitutions=_SHORT_SHA="$SHA" \
  --ignore-file=.gcloudignore \
  .
```
Expected: build SUCCESS. The migrate step picks up `h2i3j4k5l6m7` and applies it idempotently against the production DB (where the columns already exist from the diagnostic patch).

- [ ] **Step 7: Post-deploy verification**

Run:
```bash
python3 <<'EOF'
import urllib.request, urllib.parse, json
from datetime import datetime, timedelta, timezone

base = 'https://dental-api-v2-qkwzgio7eq-pd.a.run.app'
H = {"X-Clinic-Id": "market-mall-denture"}
edm = timezone(timedelta(hours=-6))

def hit(path):
    req = urllib.request.Request(base + path, headers=H)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read().decode())

def has_date(slots, dstr):
    return any(s.startswith(dstr) for s in slots)

# Next Wednesday (2026-06-03 from a recent run)
sat = (datetime.now(edm) + timedelta(days=(5 - datetime.now(edm).weekday()) % 7 or 7))
sat = sat.replace(hour=9, minute=0, second=0, microsecond=0)
end = sat + timedelta(days=1)
sdt = urllib.parse.quote(sat.isoformat(), safe='')
edt = urllib.parse.quote(end.isoformat(), safe='')

code, d = hit(f"/api/calendar/slots?start_datetime={sdt}&end_datetime={edt}&slot_minutes=30")
print(f"Saturday probe HTTP {code}")
for p in d.get('providers', []):
    print(f"  {p.get('title','?')} (id={p['provider_id']}): {len(p['slots'])} slots — should be 0")
EOF
```
Expected: each provider has 0 slots on Saturday. If non-zero, the deployment did not pick up the new engine — check Cloud Run revision.

- [ ] **Step 8: Final commit (deploy verified)**

```bash
git commit --allow-empty -m "chore(slot_engine): post-deploy verification passed"
```

---

## Done

After Task 10:
- `services/slot_engine/` is the source of truth for slot computation.
- `tools/slot_utils.py` is a 3-line shim (delete in a follow-up release).
- The `provider_busy_blocks` columns are alembic-tracked.
- v3 voice agent prefetch will get correct slots respecting the schedule.

Out-of-scope follow-ups (separate PRs, not blocking this work):
- Drop `clinic.working_hour_start/end` columns after one release confirms nothing reads them.
- Delete `tools/slot_utils.py` shim after confirming no `tools.slot_utils` imports remain in dental-agent.
- Per-provider lunch overrides if a clinic ever asks.

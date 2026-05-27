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

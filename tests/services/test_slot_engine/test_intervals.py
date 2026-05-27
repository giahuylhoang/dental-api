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

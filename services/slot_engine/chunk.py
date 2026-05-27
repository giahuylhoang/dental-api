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

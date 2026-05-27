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

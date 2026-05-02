"""v1.1 schema polish — additive tables and helpers for denturist domain fitness.

Everything in this package is purely additive on top of v1 + tracks 1-3.
No existing column is altered, no existing API response shape changes. See
~/.claude/plans/now-i-want-to-fizzy-valley.md for the full design.
"""
from database.v1_1 import models  # noqa: F401

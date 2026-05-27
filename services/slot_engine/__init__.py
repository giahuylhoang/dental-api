"""Slot engine package — composable per-day, per-provider availability."""
from services.slot_engine.engine import (
    find_busy_block_overlap,
    get_available_slots,
    resolve_providers,
)

__all__ = ["get_available_slots", "find_busy_block_overlap", "resolve_providers"]

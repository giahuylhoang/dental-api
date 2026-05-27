"""Shim — slot logic moved to services.slot_engine.

This module is kept for one release cycle so callers using
`from tools.slot_utils import get_available_slots / find_busy_block_overlap`
don't need to change immediately. Delete this file once no imports
of `tools.slot_utils` remain in either dental-api or dental-agent.
"""
from services.slot_engine import find_busy_block_overlap, get_available_slots  # noqa: F401

__all__ = ["get_available_slots", "find_busy_block_overlap"]

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

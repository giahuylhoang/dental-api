"""Hybrid SMS reply parser.

Stage 1 (this task, B4): regex matrix over normalized text. Cheap and
deterministic; expected to cover ~95% of replies.

Stage 2 (next task, B5): LLM fallback via Gemini Flash for anything
the regex doesn't match.
"""
from __future__ import annotations

import re
from enum import Enum


class ReplyIntent(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    AMBIGUOUS = "ambiguous"


_CONFIRMED_PATTERNS = [
    re.compile(r"^(y|yes|yeah|yep|ok|okay|confirm|sure|👍)$", re.IGNORECASE),
    re.compile(r"^(haan|ji|haa|haanji)$", re.IGNORECASE),   # pa/hi Latin-script
    re.compile(r"^(naam|aiwa|na'?am)$", re.IGNORECASE),     # ar Latin-script
]

_CANCELLED_PATTERNS = [
    re.compile(r"^(n|no|nope|cancel|nah)$", re.IGNORECASE),
    re.compile(r"^(nahi|nahin|nai)$", re.IGNORECASE),       # pa/hi Latin-script
    re.compile(r"^(la|laa)$", re.IGNORECASE),               # ar Latin-script
]

_RESCHEDULE_PATTERNS = [
    re.compile(r"\b(reschedule|move|change|switch|different|another)\b", re.IGNORECASE),
]


def _normalize(text: str) -> str:
    return text.strip()


def parse(text: str) -> tuple[ReplyIntent, str]:
    """Return (intent, parser_source) where source is 'regex' or 'llm'."""
    norm = _normalize(text)
    if not norm:
        return ReplyIntent.AMBIGUOUS, "regex"
    for pat in _CONFIRMED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CONFIRMED, "regex"
    for pat in _CANCELLED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CANCELLED, "regex"
    for pat in _RESCHEDULE_PATTERNS:
        if pat.search(norm):
            return ReplyIntent.RESCHEDULE_REQUESTED, "regex"
    return ReplyIntent.AMBIGUOUS, "regex"

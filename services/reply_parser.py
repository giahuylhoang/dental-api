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
    # Stage 2: LLM fallback (opt-in via env flag)
    if os.getenv("SMS_REPLY_LLM_FALLBACK", "false").lower() == "true":
        try:
            return _classify_via_llm(norm), "llm"
        except Exception as exc:
            logger.warning("LLM fallback failed: %s", exc)
            return ReplyIntent.AMBIGUOUS, "llm"
    return ReplyIntent.AMBIGUOUS, "regex"


import os
import logging

logger = logging.getLogger(__name__)

_LLM_FALLBACK_PROMPT = (
    "Classify this SMS reply to an appointment confirmation request. "
    "Reply with ONE word from this set: CONFIRMED, CANCELLED, "
    "RESCHEDULE_REQUESTED, AMBIGUOUS.\n\nSMS: {text}"
)


def _classify_via_llm(text: str) -> ReplyIntent:
    """Call Gemini 2.5 Flash to classify. Returns ReplyIntent or AMBIGUOUS on parse failure."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=_LLM_FALLBACK_PROMPT.format(text=text),
    )
    raw = (resp.text or "").strip().upper()
    if raw.startswith("CONFIRMED"):
        return ReplyIntent.CONFIRMED
    if raw.startswith("CANCELLED"):
        return ReplyIntent.CANCELLED
    if raw.startswith("RESCHEDULE"):
        return ReplyIntent.RESCHEDULE_REQUESTED
    return ReplyIntent.AMBIGUOUS

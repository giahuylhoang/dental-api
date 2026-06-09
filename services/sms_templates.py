"""Load + render SMS templates from templates/sms/<intent>.<lang>.txt.

Templates use simple {placeholder} substitution via str.format_map.
Missing language files fall back to English. Unknown intent raises
KeyError so misuse is loud.
"""
from __future__ import annotations

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "sms"
_KNOWN_INTENTS = {"reminder", "ack_confirmed", "ack_cancelled", "ack_reschedule", "ack_ambiguous"}


def _path(intent: str, lang: str) -> Path:
    return _TEMPLATE_DIR / f"{intent}.{lang}.txt"


def render(intent: str, lang: str, **vars) -> str:
    if intent not in _KNOWN_INTENTS:
        raise KeyError(f"unknown SMS intent: {intent!r}")
    p = _path(intent, lang)
    if not p.exists():
        p = _path(intent, "en")
    body = p.read_text().rstrip("\n")
    return body.format_map(_Defaultdict(vars))


class _Defaultdict(dict):
    def __missing__(self, key):
        return "{" + key + "}"

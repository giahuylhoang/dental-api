"""Tests for services/reply_parser.py.

Phase 1: regex matrix only. LLM fallback added in B5.
"""

import pytest
from services.reply_parser import parse, ReplyIntent


@pytest.mark.parametrize("text", ["yes", "Y", "yeah", "yep", "ok", "okay", "Confirm", "👍"])
def test_parse_confirmed_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.CONFIRMED
    assert source == "regex"


@pytest.mark.parametrize("text", ["no", "N", "nope", "Cancel", "nah"])
def test_parse_cancelled_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.CANCELLED


@pytest.mark.parametrize("text", ["reschedule", "I want to move it", "change my appt", "switch to next week", "another day"])
def test_parse_reschedule_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.RESCHEDULE_REQUESTED


@pytest.mark.parametrize("text", ["haan", "ji", "haa"])
def test_parse_confirmed_via_hindi_punjabi_latin(text):
    intent, _ = parse(text)
    assert intent == ReplyIntent.CONFIRMED


@pytest.mark.parametrize("text", ["nahi", "nahin", "nai"])
def test_parse_cancelled_via_hindi_punjabi_latin(text):
    intent, _ = parse(text)
    assert intent == ReplyIntent.CANCELLED


def test_parse_returns_ambiguous_for_freeform_without_regex_match():
    """Freeform text not covered by regex → falls through; LLM disabled in this task → AMBIGUOUS."""
    intent, source = parse("can we do something next Tuesday afternoon")
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "regex"

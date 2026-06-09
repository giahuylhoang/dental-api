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


from unittest.mock import patch


def test_freeform_text_falls_back_to_llm_when_enabled(monkeypatch):
    monkeypatch.setenv("SMS_REPLY_LLM_FALLBACK", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    with patch("services.reply_parser._classify_via_llm", return_value=ReplyIntent.RESCHEDULE_REQUESTED) as mock_llm:
        intent, source = parse("can we do something next Tuesday afternoon")
    assert intent == ReplyIntent.RESCHEDULE_REQUESTED
    assert source == "llm"
    mock_llm.assert_called_once()


def test_llm_fallback_returns_ambiguous_on_classifier_error(monkeypatch):
    monkeypatch.setenv("SMS_REPLY_LLM_FALLBACK", "true")
    with patch("services.reply_parser._classify_via_llm", side_effect=Exception("boom")):
        intent, source = parse("blah blah")
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "llm"  # we attempted, just failed


def test_llm_fallback_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SMS_REPLY_LLM_FALLBACK", raising=False)
    with patch("services.reply_parser._classify_via_llm") as mock_llm:
        intent, source = parse("can we do something next Tuesday afternoon")
    mock_llm.assert_not_called()
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "regex"

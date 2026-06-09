"""Tests for services/sms_templates.py loader + render."""

import pytest


def test_render_reminder_en_substitutes_all_placeholders():
    from services.sms_templates import render
    out = render(
        "reminder", "en",
        first_name="Asim", clinic_name="Market Mall",
        when_human="Tue June 10 at 2 PM",
        provider_first_name="Soheil",
        reschedule_link="https://example.com/p/reschedule/tok123",
    )
    assert "Asim" in out
    assert "Market Mall" in out
    assert "Soheil" in out
    assert "Tue June 10 at 2 PM" in out
    assert "https://example.com/p/reschedule/tok123" in out


def test_render_falls_back_to_english_when_language_missing():
    from services.sms_templates import render
    out_pa = render("ack_confirmed", "pa", when_human="Tue 2 PM")
    out_en = render("ack_confirmed", "en", when_human="Tue 2 PM")
    assert out_pa == out_en  # pa file doesn't exist yet → falls back


def test_render_raises_keyerror_on_unknown_intent():
    from services.sms_templates import render
    with pytest.raises(KeyError):
        render("not_a_real_intent", "en")


def test_render_preserves_missing_placeholders_for_partial_vars():
    """When a placeholder var is missing, it's preserved as-is so callers
    can spot the omission (vs crashing at send time)."""
    from services.sms_templates import render
    out = render("ack_confirmed", "en")  # no when_human passed
    assert "{when_human}" in out

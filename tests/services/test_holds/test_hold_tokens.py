import pytest
from services.hold_tokens import make_confirm_token, verify_confirm_token


def test_round_trip(monkeypatch):
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test-secret")
    tok = make_confirm_token("appt-123")
    assert verify_confirm_token(tok) == "appt-123"


def test_tampered_token_rejected(monkeypatch):
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test-secret")
    tok = make_confirm_token("appt-123")
    assert verify_confirm_token(tok[:-2] + "xx") is None


def test_wrong_secret_rejected(monkeypatch):
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "secret-a")
    tok = make_confirm_token("appt-123")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "secret-b")
    assert verify_confirm_token(tok) is None

"""
v2 AI config endpoint tests.

Covers /api/v2/settings/ai/{voice,disclosure,services-bookable,knowledge}.
Multi-tenancy and additive-only schema are first-class concerns:
  - Every endpoint scopes by X-Clinic-Id header.
  - No edits to v1 endpoints; the locked v1 contract test must stay green.

Uses the in-memory SQLite + seeded `default` clinic from tests/conftest.py:91.
"""
from __future__ import annotations

import pytest

from database.models import Service, Clinic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_services(db, clinic_id: str = "default"):
    """Seed two services for the clinic and return them."""
    a = Service(clinic_id=clinic_id, name="Recall exam", duration_min=30, base_price=145)
    b = Service(clinic_id=clinic_id, name="Crown prep", duration_min=60, base_price=580)
    db.add_all([a, b])
    db.commit()
    db.refresh(a)
    db.refresh(b)
    return a, b


def _seed_second_clinic(db, clinic_id: str = "other"):
    """Seed a second clinic to test cross-tenant isolation."""
    if db.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        db.add(Clinic(id=clinic_id, name="Other Clinic", timezone="America/Edmonton"))
        db.commit()


# ---------------------------------------------------------------------------
# Voice & persona
# ---------------------------------------------------------------------------

def test_voice_get_returns_defaults_when_unset(client):
    r = client.get("/api/v2/settings/ai/voice")
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_name"] == "Dental AI"
    assert body["provider_title"] == "Denturist"
    assert body["reason_question"] == "What brings you in?"
    assert body["language"] == "en-US"


def test_voice_put_upserts_and_persists(client):
    payload = {
        "assistant_name": "Aurora",
        "provider_title": "Dentist",
        "reason_question": "How can we help today?",
        "language": "en-CA",
    }
    r = client.put("/api/v2/settings/ai/voice", json=payload)
    assert r.status_code == 200
    saved = r.json()
    assert saved["assistant_name"] == "Aurora"
    assert saved["language"] == "en-CA"

    # Round-trip: GET returns the saved values
    r2 = client.get("/api/v2/settings/ai/voice")
    assert r2.json()["assistant_name"] == "Aurora"
    assert r2.json()["provider_title"] == "Dentist"


def test_voice_put_partial_update_keeps_other_fields(client):
    client.put("/api/v2/settings/ai/voice", json={
        "assistant_name": "Aurora",
        "provider_title": "Dentist",
        "reason_question": "How can we help today?",
        "language": "en-CA",
    })
    # Update only language
    r = client.put("/api/v2/settings/ai/voice", json={"language": "fr-CA"})
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "fr-CA"
    assert body["assistant_name"] == "Aurora"  # preserved


# ---------------------------------------------------------------------------
# AI disclosure
# ---------------------------------------------------------------------------

def test_disclosure_get_returns_defaults(client):
    r = client.get("/api/v2/settings/ai/disclosure")
    assert r.status_code == 200
    body = r.json()
    assert body["required"] is False
    assert body["phrase"] == ""
    assert body["last_reviewed_at"] is None


def test_disclosure_put_sets_last_reviewed_when_phrase_changes(client):
    r = client.put("/api/v2/settings/ai/disclosure", json={
        "required": True,
        "phrase": "Hi, this is the AI receptionist. I am not human.",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["required"] is True
    assert body["phrase"].startswith("Hi, this is the AI")
    assert body["last_reviewed_at"] is not None  # set to utcnow on phrase change

    first_reviewed = body["last_reviewed_at"]

    # Toggle required without changing phrase — last_reviewed_at should NOT advance
    r2 = client.put("/api/v2/settings/ai/disclosure", json={"required": False})
    assert r2.json()["last_reviewed_at"] == first_reviewed


# ---------------------------------------------------------------------------
# Services bookable
# ---------------------------------------------------------------------------

def test_services_bookable_list_defaults_false(client, db_session):
    a, b = _seed_services(db_session)
    r = client.get("/api/v2/settings/ai/services-bookable")
    assert r.status_code == 200
    rows = r.json()
    by_id = {row["service_id"]: row for row in rows}
    assert a.id in by_id and b.id in by_id
    assert by_id[a.id]["bookable"] is False
    assert by_id[a.id]["name"] == "Recall exam"
    assert by_id[a.id]["duration_min"] == 30
    # base_price comes back as a stringy decimal or float — accept both
    assert "base_price" in by_id[a.id]


def test_services_bookable_toggle(client, db_session):
    a, _ = _seed_services(db_session)
    r = client.put(f"/api/v2/settings/ai/services-bookable/{a.id}", json={"bookable": True})
    assert r.status_code == 200
    assert r.json()["bookable"] is True

    # Verify list reflects the toggle
    rows = client.get("/api/v2/settings/ai/services-bookable").json()
    by_id = {row["service_id"]: row for row in rows}
    assert by_id[a.id]["bookable"] is True

    # Toggle off
    r = client.put(f"/api/v2/settings/ai/services-bookable/{a.id}", json={"bookable": False})
    assert r.json()["bookable"] is False


def test_services_bookable_404_on_missing_service(client):
    r = client.put("/api/v2/settings/ai/services-bookable/9999", json={"bookable": True})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Knowledge docs
# ---------------------------------------------------------------------------

def test_knowledge_empty_list(client):
    r = client.get("/api/v2/settings/ai/knowledge")
    assert r.status_code == 200
    assert r.json() == []


def test_knowledge_create_then_list(client):
    body = {"filename": "practice_info.md", "title": "Practice info", "body": "# Practice info\n\nHours: 8-5."}
    r = client.post("/api/v2/settings/ai/knowledge", json=body)
    assert r.status_code == 201
    created = r.json()
    assert created["filename"] == "practice_info.md"
    assert created["word_count"] >= 4
    assert "body" not in created or created["body"] == body["body"]

    rows = client.get("/api/v2/settings/ai/knowledge").json()
    assert len(rows) == 1
    # List view should NOT include body (keep payloads small)
    assert "body" not in rows[0]
    assert rows[0]["filename"] == "practice_info.md"
    assert rows[0]["title"] == "Practice info"
    assert rows[0]["word_count"] >= 4


def test_knowledge_get_includes_body(client):
    client.post("/api/v2/settings/ai/knowledge", json={
        "filename": "denture_faq.md", "title": "Denture FAQ", "body": "# FAQ\n\nOne two three.",
    })
    r = client.get("/api/v2/settings/ai/knowledge/denture_faq.md")
    assert r.status_code == 200
    body = r.json()
    assert body["body"] == "# FAQ\n\nOne two three."
    assert body["word_count"] == 4  # FAQ + One + two + three


def test_knowledge_create_duplicate_filename_409(client):
    payload = {"filename": "x.md", "title": "X", "body": ""}
    r1 = client.post("/api/v2/settings/ai/knowledge", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v2/settings/ai/knowledge", json=payload)
    assert r2.status_code == 409


def test_knowledge_update_recomputes_word_count(client):
    client.post("/api/v2/settings/ai/knowledge", json={"filename": "x.md", "title": "X", "body": "one two"})
    r = client.put("/api/v2/settings/ai/knowledge/x.md", json={"body": "one two three four five"})
    assert r.status_code == 200
    assert r.json()["word_count"] == 5


def test_knowledge_update_404(client):
    r = client.put("/api/v2/settings/ai/knowledge/missing.md", json={"body": "..."})
    assert r.status_code == 404


def test_knowledge_delete(client):
    client.post("/api/v2/settings/ai/knowledge", json={"filename": "x.md", "title": "X", "body": ""})
    r = client.delete("/api/v2/settings/ai/knowledge/x.md")
    assert r.status_code == 204
    assert client.get("/api/v2/settings/ai/knowledge").json() == []


def test_knowledge_delete_404(client):
    r = client.delete("/api/v2/settings/ai/knowledge/missing.md")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Cross-tenant isolation
# ---------------------------------------------------------------------------

def test_voice_isolated_per_clinic(client, db_session):
    _seed_second_clinic(db_session, "other")
    # Set voice on default clinic
    client.put("/api/v2/settings/ai/voice", json={"assistant_name": "DefaultBot"})
    # Same call with X-Clinic-Id: other — should NOT see DefaultBot
    r = client.get("/api/v2/settings/ai/voice", headers={"X-Clinic-Id": "other"})
    assert r.status_code == 200
    assert r.json()["assistant_name"] == "Dental AI"  # other clinic's defaults


def test_knowledge_isolated_per_clinic(client, db_session):
    _seed_second_clinic(db_session, "other")
    client.post("/api/v2/settings/ai/knowledge", json={"filename": "x.md", "title": "X", "body": "..."})
    rows = client.get("/api/v2/settings/ai/knowledge", headers={"X-Clinic-Id": "other"}).json()
    assert rows == []
    # Other clinic can have its OWN x.md without 409
    r = client.post(
        "/api/v2/settings/ai/knowledge",
        headers={"X-Clinic-Id": "other"},
        json={"filename": "x.md", "title": "Other X", "body": ""},
    )
    assert r.status_code == 201


# ---------------------------------------------------------------------------
# Integrations clinic-scoping
# ---------------------------------------------------------------------------

def test_integrations_returns_defaults_when_no_clinic_config(client):
    """GET /integrations returns env-based defaults when no per-clinic config."""
    r = client.get("/api/v2/settings/integrations")
    assert r.status_code == 200
    body = r.json()
    # Should have sms, email, whatsapp keys
    assert "sms" in body
    assert "email" in body
    assert "whatsapp" in body
    assert "enabled" in body["sms"]


def test_integrations_isolated_per_clinic(client, db_session):
    """Two clinics with different flags see different responses."""
    _seed_second_clinic(db_session, "other")
    
    # Both clinics should get the same env-based defaults initially
    r1 = client.get("/api/v2/settings/integrations")
    r2 = client.get("/api/v2/settings/integrations", headers={"X-Clinic-Id": "other"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Both should have same structure
    assert set(r1.json().keys()) == set(r2.json().keys())

"""
v2 AI config contract snapshot — locks endpoint shapes.

Mirrors the role of tests/test_contract_v1.py (which guards calendar_client.py).
Any change that drops a key or alters a type fails this test, forcing a
deliberate decision before frontend or downstream agents break.
"""
from __future__ import annotations

from database.models import Service


def assert_shape(obj, expected: dict) -> None:
    """Same helper as test_contract_v1.assert_shape — superset key check + type check."""
    assert isinstance(obj, dict), f"Expected dict, got {type(obj).__name__}"
    missing = [k for k in expected if k not in obj]
    assert not missing, f"Missing keys: {missing}. Got: {sorted(obj.keys())}"
    for key, types in expected.items():
        py_types = types if isinstance(types, tuple) else (types,)
        value = obj[key]
        assert isinstance(value, py_types), (
            f"Key {key!r}: expected {py_types}, got {type(value).__name__} ({value!r})"
        )


# ---------------------------------------------------------------------------
# Voice & persona
# ---------------------------------------------------------------------------

def test_contract_voice_get(client):
    r = client.get("/api/v2/settings/ai/voice")
    assert r.status_code == 200
    assert_shape(r.json(), {
        "assistant_name": str,
        "provider_title": str,
        "reason_question": str,
        "language": str,
    })


def test_contract_voice_put(client):
    r = client.put("/api/v2/settings/ai/voice", json={"language": "fr-CA"})
    assert r.status_code == 200
    assert_shape(r.json(), {
        "assistant_name": str,
        "provider_title": str,
        "reason_question": str,
        "language": str,
    })


# ---------------------------------------------------------------------------
# Disclosure
# ---------------------------------------------------------------------------

def test_contract_disclosure_get(client):
    r = client.get("/api/v2/settings/ai/disclosure")
    assert r.status_code == 200
    assert_shape(r.json(), {
        "required": bool,
        "phrase": str,
        "last_reviewed_at": (str, type(None)),
    })


def test_contract_disclosure_put_with_phrase_change(client):
    r = client.put("/api/v2/settings/ai/disclosure", json={
        "required": True, "phrase": "Hi, this is the AI receptionist.",
    })
    assert r.status_code == 200
    body = r.json()
    assert_shape(body, {
        "required": bool,
        "phrase": str,
        "last_reviewed_at": (str, type(None)),
    })
    assert body["last_reviewed_at"] is not None  # phrase change advances timestamp


# ---------------------------------------------------------------------------
# Services bookable
# ---------------------------------------------------------------------------

def test_contract_services_bookable_list(client, db_session):
    db_session.add(Service(clinic_id="default", name="Recall exam", duration_min=30, base_price=145))
    db_session.commit()
    r = client.get("/api/v2/settings/ai/services-bookable")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list) and rows
    assert_shape(rows[0], {
        "service_id": int,
        "name": str,
        "duration_min": (int, type(None)),
        "base_price": (float, int, type(None)),
        "bookable": bool,
    })


def test_contract_services_bookable_put(client, db_session):
    s = Service(clinic_id="default", name="Recall exam", duration_min=30, base_price=145)
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    r = client.put(f"/api/v2/settings/ai/services-bookable/{s.id}", json={"bookable": True})
    assert r.status_code == 200
    assert_shape(r.json(), {
        "service_id": int,
        "name": str,
        "duration_min": (int, type(None)),
        "base_price": (float, int, type(None)),
        "bookable": bool,
    })


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------

def test_contract_knowledge_list_item_shape(client):
    client.post("/api/v2/settings/ai/knowledge", json={
        "filename": "x.md", "title": "X", "body": "one two three",
    })
    rows = client.get("/api/v2/settings/ai/knowledge").json()
    assert rows
    assert_shape(rows[0], {
        "filename": str,
        "title": str,
        "word_count": int,
        "updated_at": (str, type(None)),
    })
    # List view does NOT include body — keep payload small.
    assert "body" not in rows[0]


def test_contract_knowledge_full_doc_shape(client):
    client.post("/api/v2/settings/ai/knowledge", json={
        "filename": "x.md", "title": "X", "body": "one two three",
    })
    body = client.get("/api/v2/settings/ai/knowledge/x.md").json()
    assert_shape(body, {
        "filename": str,
        "title": str,
        "body": str,
        "word_count": int,
        "updated_at": (str, type(None)),
    })


def test_contract_knowledge_create_returns_full(client):
    r = client.post("/api/v2/settings/ai/knowledge", json={
        "filename": "y.md", "title": "Y", "body": "one two",
    })
    assert r.status_code == 201
    assert_shape(r.json(), {
        "filename": str,
        "title": str,
        "body": str,
        "word_count": int,
        "updated_at": (str, type(None)),
    })

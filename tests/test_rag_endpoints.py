"""Endpoint contract tests for /rag/answer and /clinics/{id}/faqs."""
import pytest


pytestmark = pytest.mark.pgvector


def _unit_vec_at(idx: int) -> list[float]:
    v = [0.0] * 768
    v[idx] = 1.0
    return v


def _stub_embedder(monkeypatch, vec):
    async def fake_embed(text):
        return vec
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)


def _seed_clinic(db, clinic_id: str):
    from database.models import Clinic
    if db.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        db.add(Clinic(id=clinic_id, name=clinic_id))
        db.flush()


def _clear_cache():
    """Reset the route-level TTL cache so cached responses from prior tests don't leak."""
    from api.rag.router import _cache
    _cache.clear()


def test_get_faqs_returns_seeded_rows_in_order(pg_db_session, pg_client):
    from database.ops.rag import ClinicFaq
    _seed_clinic(pg_db_session, "cf1")
    pg_db_session.add(ClinicFaq(clinic_id="cf1", question="Q2?", answer="A2", ordering=2))
    pg_db_session.add(ClinicFaq(clinic_id="cf1", question="Q1?", answer="A1", ordering=1))
    pg_db_session.flush()

    r = pg_client.get("/clinics/cf1/faqs")
    assert r.status_code == 200
    body = r.json()
    assert body["faqs"] == [
        {"question": "Q1?", "answer": "A1"},
        {"question": "Q2?", "answer": "A2"},
    ]


def test_get_faqs_unknown_clinic_returns_empty_list(pg_client):
    r = pg_client.get("/clinics/no_such_clinic/faqs")
    assert r.status_code == 200
    assert r.json() == {"faqs": []}


def test_post_rag_answer_returns_match(monkeypatch, pg_db_session, pg_client):
    _clear_cache()
    from database.ops.rag import RagDoc
    _seed_clinic(pg_db_session, "cr1")
    pg_db_session.add(RagDoc(
        clinic_id="cr1", doc_title="Reline", content="reshape denture",
        voice_ready="Relines take about an hour.",
        embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    _stub_embedder(monkeypatch, _unit_vec_at(0))
    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "cr1", "question": "How long does a reline take?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["answer"] == "Relines take about an hour."
    assert body["sources"][0]["doc_title"] == "Reline"


def test_post_rag_answer_no_match_when_clinic_empty(monkeypatch, pg_client):
    _clear_cache()
    _stub_embedder(monkeypatch, _unit_vec_at(0))
    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "empty", "question": "anything"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "no_match"


def test_rag_answer_503_when_gemini_key_missing(monkeypatch, pg_db_session, pg_client):
    _clear_cache()
    from database.ops.rag import RagDoc
    _seed_clinic(pg_db_session, "cr2")
    pg_db_session.add(RagDoc(
        clinic_id="cr2", doc_title="x", content="x",
        voice_ready=None, embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "cr2", "question": "anything"},
    )
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json().get("detail", "")


def test_rag_answer_cache_returns_same_response_without_re_embedding(monkeypatch, pg_db_session, pg_client):
    """Same (clinic_id, question) within TTL → second call must not call embed()."""
    _clear_cache()
    from database.ops.rag import RagDoc
    _seed_clinic(pg_db_session, "cr3")
    pg_db_session.add(RagDoc(
        clinic_id="cr3", doc_title="t", content="c",
        voice_ready="cached answer", embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    call_count = {"n": 0}

    async def counting_embed(text):
        call_count["n"] += 1
        return _unit_vec_at(0)

    monkeypatch.setattr("services.rag.retrieval.embed", counting_embed)

    payload = {"clinic_id": "cr3", "question": "hello?"}
    r1 = pg_client.post("/rag/answer", json=payload)
    r2 = pg_client.post("/rag/answer", json=payload)
    assert r1.json() == r2.json()
    assert call_count["n"] == 1, "embedder should be called only once due to cache"

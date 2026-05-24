"""Tests for services.rag.retrieval.answer — embedding-based top-1 retrieval."""
import asyncio
import pytest

from database.ops.rag import RagDoc


pytestmark = pytest.mark.pgvector


def _unit_vec_at(idx: int, dim: int = 768) -> list[float]:
    v = [0.0] * dim
    v[idx] = 1.0
    return v


def _seed_clinic(pg_db_session, clinic_id: str):
    """Idempotently ensure a clinic row exists so FK constraints are satisfied."""
    from database.models import Clinic
    if pg_db_session.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        pg_db_session.add(Clinic(id=clinic_id, name=clinic_id))
        pg_db_session.flush()


def test_answer_returns_ok_for_close_match(monkeypatch, pg_db_session):
    _seed_clinic(pg_db_session, "c1")
    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="Reline care",
        content="A reline reshapes the inside of your existing denture.",
        voice_ready="A reline reshapes the inside of your denture. Most relines take about an hour.",
        embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="Unrelated",
        content="Something else.", voice_ready=None,
        embedding=_unit_vec_at(100), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        return _unit_vec_at(0)
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "c1", "what is a reline?"))

    assert result["status"] == "ok"
    assert "reline" in result["answer"].lower()
    assert result["confidence"] >= 0.6
    assert result["sources"][0]["doc_title"] == "Reline care"


def test_answer_returns_no_match_below_threshold(monkeypatch, pg_db_session):
    _seed_clinic(pg_db_session, "c1")
    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="A", content="foo", voice_ready=None,
        embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        return _unit_vec_at(500)
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "c1", "totally unrelated"))

    assert result["status"] == "no_match"
    assert result["answer"] == ""
    assert result["sources"] == []


def test_answer_isolates_per_clinic(monkeypatch, pg_db_session):
    _seed_clinic(pg_db_session, "clinic_a")
    _seed_clinic(pg_db_session, "clinic_b")
    pg_db_session.add(RagDoc(
        clinic_id="clinic_b", doc_title="B-only", content="hidden",
        voice_ready=None, embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        return _unit_vec_at(0)
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "clinic_a", "anything"))

    assert result["status"] == "no_match"
    assert result["sources"] == []


def test_answer_returns_no_match_when_clinic_has_no_docs(monkeypatch, pg_db_session):
    _seed_clinic(pg_db_session, "empty_clinic")

    async def fake_embed(text):
        return _unit_vec_at(0)
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "empty_clinic", "anything"))

    assert result["status"] == "no_match"
    assert result["sources"] == []

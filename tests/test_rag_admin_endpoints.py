"""Admin CRUD for clinic_faqs and rag_docs (writes from admin-api / portal)."""
import pytest

from database.ops.rag import RagDoc


pytestmark = pytest.mark.pgvector


def _unit_vec_at(idx: int) -> list[float]:
    v = [0.0] * 768
    v[idx] = 1.0
    return v


def _seed_clinic(db, clinic_id: str):
    from database.models import Clinic
    if db.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        db.add(Clinic(id=clinic_id, name=clinic_id))
        db.flush()


def _override_embed_store(monkeypatch, pg_db_session, vec):
    """Replace `_embed_and_store` with a coroutine that uses the test session.

    Why: the real `_embed_and_store` opens a fresh `SessionLocal()` whose
    engine isn't bound to the test's transactional connection. In the test we
    care about the contract (background task fires; embedding gets filled),
    not the production session-creation path — that's exercised in the
    live smoke in Task 9.
    """
    async def fake_store(doc_id: int, content: str):
        row = pg_db_session.query(RagDoc).filter(RagDoc.id == doc_id).first()
        if row is not None:
            row.embedding = vec
            pg_db_session.flush()
    monkeypatch.setattr("api.admin.rag_router._embed_and_store", fake_store)


def test_post_faq_creates_row(pg_db_session, pg_client):
    _seed_clinic(pg_db_session, "ac1")
    r = pg_client.post(
        "/admin/clinics/ac1/faqs",
        json={"question": "Hours?", "answer": "9-5", "ordering": 1},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["question"] == "Hours?"
    assert body["ordering"] == 1
    assert body["id"] > 0


def test_patch_faq_updates_row(pg_db_session, pg_client):
    _seed_clinic(pg_db_session, "ac2")
    created = pg_client.post(
        "/admin/clinics/ac2/faqs",
        json={"question": "x", "answer": "y", "ordering": 0},
    ).json()
    r = pg_client.patch(
        f"/admin/clinics/ac2/faqs/{created['id']}",
        json={"answer": "z"},
    )
    assert r.status_code == 200
    assert r.json()["answer"] == "z"


def test_delete_faq(pg_db_session, pg_client):
    _seed_clinic(pg_db_session, "ac3")
    created = pg_client.post(
        "/admin/clinics/ac3/faqs",
        json={"question": "x", "answer": "y", "ordering": 0},
    ).json()
    r = pg_client.delete(f"/admin/clinics/ac3/faqs/{created['id']}")
    assert r.status_code == 204
    list_r = pg_client.get("/clinics/ac3/faqs")
    assert list_r.json()["faqs"] == []


def test_post_rag_doc_returns_202_and_schedules_embed(monkeypatch, pg_client, pg_db_session):
    _seed_clinic(pg_db_session, "ar1")
    _override_embed_store(monkeypatch, pg_db_session, _unit_vec_at(7))

    r = pg_client.post(
        "/admin/clinics/ar1/rag_docs",
        json={"doc_title": "Reline care", "content": "A reline reshapes..."},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["id"] > 0
    assert body["embedding_ready"] is True

    row = pg_db_session.query(RagDoc).filter(RagDoc.id == body["id"]).first()
    assert row is not None
    assert row.embedding is not None
    assert len(row.embedding) == 768


def test_patch_rag_doc_content_re_embeds(monkeypatch, pg_client, pg_db_session):
    _seed_clinic(pg_db_session, "ar2")
    _override_embed_store(monkeypatch, pg_db_session, _unit_vec_at(7))
    created = pg_client.post(
        "/admin/clinics/ar2/rag_docs",
        json={"doc_title": "t", "content": "v1"},
    ).json()

    _override_embed_store(monkeypatch, pg_db_session, _unit_vec_at(42))
    r = pg_client.patch(
        f"/admin/clinics/ar2/rag_docs/{created['id']}",
        json={"content": "v2"},
    )
    assert r.status_code == 200

    pg_db_session.expire_all()
    row = pg_db_session.query(RagDoc).filter(RagDoc.id == created["id"]).first()
    assert row.content == "v2"
    assert row.embedding[42] == pytest.approx(1.0)
    assert row.embedding[7] == pytest.approx(0.0)


def test_delete_rag_doc(monkeypatch, pg_client, pg_db_session):
    _seed_clinic(pg_db_session, "ar3")
    _override_embed_store(monkeypatch, pg_db_session, _unit_vec_at(0))
    created = pg_client.post(
        "/admin/clinics/ar3/rag_docs",
        json={"doc_title": "t", "content": "c"},
    ).json()
    r = pg_client.delete(f"/admin/clinics/ar3/rag_docs/{created['id']}")
    assert r.status_code == 204

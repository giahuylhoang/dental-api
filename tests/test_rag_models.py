"""Model round-trip tests for clinic_faqs and rag_docs (require pgvector)."""
import os
import pytest


pytestmark = pytest.mark.pgvector


def test_clinic_faq_insert_and_query(pg_db_session):
    from database.ops.rag import ClinicFaq

    row = ClinicFaq(
        clinic_id="t_clinic",
        question="Hours?",
        answer="Monday to Friday, nine to five.",
        ordering=1,
    )
    pg_db_session.add(row)
    pg_db_session.flush()

    got = (
        pg_db_session.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == "t_clinic")
        .order_by(ClinicFaq.ordering)
        .all()
    )
    assert len(got) == 1
    assert got[0].question == "Hours?"
    assert got[0].answer.startswith("Monday")


def test_rag_doc_insert_with_vector(pg_db_session):
    from database.ops.rag import RagDoc

    vec = [0.0] * 768
    vec[0] = 1.0
    row = RagDoc(
        clinic_id="t_clinic",
        doc_title="Reline care",
        content="A reline reshapes the inside of your existing denture.",
        voice_ready=None,
        embedding=vec,
        doc_metadata={"category": "post-op"},
    )
    pg_db_session.add(row)
    pg_db_session.flush()

    got = pg_db_session.query(RagDoc).filter(RagDoc.clinic_id == "t_clinic").first()
    assert got is not None
    assert got.doc_title == "Reline care"
    assert len(got.embedding) == 768
    assert got.embedding[0] == pytest.approx(1.0)

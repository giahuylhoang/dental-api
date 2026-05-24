"""Embedding-based RAG retrieval against the rag_docs table.

Public function: `answer(db, clinic_id, question) -> dict` matching the
canonical API contract (status / answer / confidence / sources).
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.rag.embeddings import embed

_CONFIDENCE_THRESHOLD = 0.6
_TOP_K = 5
_EXCERPT_CHARS = 600


async def answer(db: Session, clinic_id: str, question: str) -> dict:
    """Embed the question, find the closest rag_doc for this clinic, return
    the voice-formatted answer if confidence is above the threshold.

    Confidence = 1 - cosine_distance (cosine_distance is what pgvector's <=> returns).
    """
    q_embed = await embed(question)

    rows = db.execute(
        text(
            """
            SELECT id, doc_title, content, voice_ready,
                   (embedding <=> CAST(:q AS vector)) AS distance
            FROM rag_docs
            WHERE clinic_id = :cid AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:q AS vector)
            LIMIT :k
            """
        ),
        {"q": str(q_embed), "cid": clinic_id, "k": _TOP_K},
    ).fetchall()

    if not rows:
        return {"status": "no_match", "answer": "", "confidence": 0.0, "sources": []}

    top = rows[0]
    confidence = max(0.0, 1.0 - float(top.distance))
    if confidence < _CONFIDENCE_THRESHOLD:
        return {"status": "no_match", "answer": "", "confidence": confidence, "sources": []}

    answer_text = top.voice_ready or _excerpt(top.content)
    sources = [
        {"doc_id": int(r.id), "doc_title": r.doc_title,
         "score": round(max(0.0, 1.0 - float(r.distance)), 4)}
        for r in rows
    ]
    return {"status": "ok", "answer": answer_text,
            "confidence": round(confidence, 4), "sources": sources}


def _excerpt(content: str) -> str:
    """Trim content to ~_EXCERPT_CHARS at a sentence boundary if possible."""
    if len(content) <= _EXCERPT_CHARS:
        return content
    cut = content[:_EXCERPT_CHARS]
    last_dot = cut.rfind(". ")
    if last_dot > _EXCERPT_CHARS // 2:
        return cut[: last_dot + 1]
    return cut + "…"

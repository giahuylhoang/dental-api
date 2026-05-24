"""Read endpoints for the Clinic Q&A RAG feature.

  GET  /clinics/{clinic_id}/faqs
  POST /rag/answer

Both unauthenticated for now — the voice agent calls these via the shared
CalendarClient using an X-Clinic-Id header for trace correlation only. Auth
can be layered on later once the admin frontend / portal is the only other
caller.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.ops.rag import ClinicFaq
from services.rag.embeddings import MissingGeminiKey, EmbeddingError
from services.rag.retrieval import answer as retrieve_answer


router = APIRouter(tags=["rag"])


# ---------- /clinics/{clinic_id}/faqs ----------


class FaqOut(BaseModel):
    question: str
    answer: str


class FaqsResponse(BaseModel):
    faqs: list[FaqOut]


@router.get("/clinics/{clinic_id}/faqs", response_model=FaqsResponse)
def get_clinic_faqs(clinic_id: str, db: Session = Depends(get_db)) -> FaqsResponse:
    rows = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id)
        .order_by(ClinicFaq.ordering, ClinicFaq.id)
        .all()
    )
    return FaqsResponse(faqs=[FaqOut(question=r.question, answer=r.answer) for r in rows])


# ---------- /rag/answer ----------


class AnswerRequest(BaseModel):
    clinic_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)


class AnswerSource(BaseModel):
    doc_id: int
    doc_title: str
    score: float


class AnswerResponse(BaseModel):
    status: str
    answer: str
    confidence: float
    sources: list[AnswerSource]


_CACHE_TTL_SECONDS = 60
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def _normalize_q(q: str) -> str:
    return " ".join(q.lower().split())


@router.post("/rag/answer", response_model=AnswerResponse)
async def post_rag_answer(body: AnswerRequest, db: Session = Depends(get_db)) -> AnswerResponse:
    key = (body.clinic_id, _normalize_q(body.question))
    now = time.monotonic()
    hit = _cache.get(key)
    if hit is not None and (now - hit[0]) < _CACHE_TTL_SECONDS:
        return AnswerResponse(**hit[1])

    try:
        result = await retrieve_answer(db, body.clinic_id, body.question)
    except MissingGeminiKey as e:
        raise HTTPException(status_code=503, detail=f"GEMINI_API_KEY not configured: {e}") from e
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding upstream error: {e}") from e

    _cache[key] = (now, result)
    return AnswerResponse(**result)

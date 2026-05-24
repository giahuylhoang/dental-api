"""Admin CRUD for the Clinic Q&A RAG feature.

  POST   /admin/clinics/{clinic_id}/faqs                  → 201 + created row
  PATCH  /admin/clinics/{clinic_id}/faqs/{faq_id}         → 200 + updated row
  DELETE /admin/clinics/{clinic_id}/faqs/{faq_id}         → 204

  POST   /admin/clinics/{clinic_id}/rag_docs              → 202 + row (embedding filled in background)
  PATCH  /admin/clinics/{clinic_id}/rag_docs/{doc_id}     → 200 (re-embeds if content changed)
  DELETE /admin/clinics/{clinic_id}/rag_docs/{doc_id}     → 204

No auth in this commit — admin-api / portal will sit in front of these. Add
clinic-scoping middleware later.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.ops.rag import ClinicFaq, RagDoc
from services.rag.embeddings import embed


router = APIRouter(prefix="/admin/clinics", tags=["admin-rag"])


# ---------- FAQ schemas ----------


class FaqCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    ordering: int = 0


class FaqPatch(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    ordering: Optional[int] = None


class FaqRow(BaseModel):
    id: int
    clinic_id: str
    question: str
    answer: str
    ordering: int


def _faq_out(row: ClinicFaq) -> FaqRow:
    return FaqRow(
        id=row.id, clinic_id=row.clinic_id, question=row.question,
        answer=row.answer, ordering=row.ordering,
    )


# ---------- FAQ endpoints ----------


@router.post("/{clinic_id}/faqs", response_model=FaqRow, status_code=201)
def create_faq(clinic_id: str, body: FaqCreate, db: Session = Depends(get_db)):
    row = ClinicFaq(
        clinic_id=clinic_id,
        question=body.question, answer=body.answer, ordering=body.ordering,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _faq_out(row)


@router.patch("/{clinic_id}/faqs/{faq_id}", response_model=FaqRow)
def patch_faq(clinic_id: str, faq_id: int, body: FaqPatch, db: Session = Depends(get_db)):
    row = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id, ClinicFaq.id == faq_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found in clinic {clinic_id}")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(row, field, val)
    db.commit()
    db.refresh(row)
    return _faq_out(row)


@router.delete("/{clinic_id}/faqs/{faq_id}", status_code=204)
def delete_faq(clinic_id: str, faq_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id, ClinicFaq.id == faq_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found in clinic {clinic_id}")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


# ---------- RAG doc schemas ----------


class RagDocCreate(BaseModel):
    doc_title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    voice_ready: Optional[str] = None


class RagDocPatch(BaseModel):
    doc_title: Optional[str] = None
    content: Optional[str] = None
    voice_ready: Optional[str] = None


class RagDocCreatedOut(BaseModel):
    id: int
    clinic_id: str
    doc_title: str
    embedding_ready: bool


class RagDocRow(BaseModel):
    id: int
    clinic_id: str
    doc_title: str
    content: str
    voice_ready: Optional[str]
    has_embedding: bool


def _doc_full(row: RagDoc) -> RagDocRow:
    return RagDocRow(
        id=row.id, clinic_id=row.clinic_id, doc_title=row.doc_title,
        content=row.content, voice_ready=row.voice_ready,
        has_embedding=row.embedding is not None,
    )


# ---------- RAG doc endpoints ----------


async def _embed_and_store(doc_id: int, text: str):
    """Background task body: re-open a session, embed, write back."""
    from database.connection import SessionLocal
    vec = await embed(text)
    db = SessionLocal()
    try:
        row = db.query(RagDoc).filter(RagDoc.id == doc_id).first()
        if row is not None:
            row.embedding = vec
            db.commit()
    finally:
        db.close()


@router.post("/{clinic_id}/rag_docs", response_model=RagDocCreatedOut, status_code=202)
async def create_rag_doc(
    clinic_id: str,
    body: RagDocCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    row = RagDoc(
        clinic_id=clinic_id,
        doc_title=body.doc_title, content=body.content, voice_ready=body.voice_ready,
        doc_metadata={},
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    background.add_task(_embed_and_store, row.id, body.content)
    return RagDocCreatedOut(
        id=row.id, clinic_id=row.clinic_id, doc_title=row.doc_title,
        embedding_ready=True,
    )


@router.patch("/{clinic_id}/rag_docs/{doc_id}", response_model=RagDocRow)
async def patch_rag_doc(
    clinic_id: str, doc_id: int, body: RagDocPatch,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    row = (
        db.query(RagDoc)
        .filter(RagDoc.clinic_id == clinic_id, RagDoc.id == doc_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"rag_doc {doc_id} not found")

    updates = body.model_dump(exclude_unset=True)
    content_changed = "content" in updates and updates["content"] != row.content
    for field, val in updates.items():
        setattr(row, field, val)
    db.commit()
    db.refresh(row)

    if content_changed:
        background.add_task(_embed_and_store, row.id, row.content)

    return _doc_full(row)


@router.delete("/{clinic_id}/rag_docs/{doc_id}", status_code=204)
def delete_rag_doc(clinic_id: str, doc_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(RagDoc)
        .filter(RagDoc.clinic_id == clinic_id, RagDoc.id == doc_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"rag_doc {doc_id} not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)

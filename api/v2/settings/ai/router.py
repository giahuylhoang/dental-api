"""
v2 Settings · AI Receptionist configuration router.

Endpoints under /api/v2/settings/ai/:
  - voice              GET, PUT
  - disclosure         GET, PUT
  - services-bookable  GET, PUT /{service_id}
  - knowledge          GET (list), POST, GET/PUT/DELETE /{filename}

All endpoints scope by clinic via the `get_clinic` dep (api/main.py:43).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Service
from database.ops.ai_config import (
    ClinicAiVoice,
    ClinicAiDisclosure,
    ServiceAiBookable,
    ClinicKnowledgeDoc,
)
from api.main import get_clinic
from api.caching import add_cache_headers, check_etag

router = APIRouter(prefix="/ai", tags=["v2-settings-ai"])


# ---------------------------------------------------------------------------
# Voice & persona
# ---------------------------------------------------------------------------

class VoiceOut(BaseModel):
    assistant_name: str
    provider_title: str
    reason_question: str
    language: str


class VoicePatch(BaseModel):
    assistant_name: Optional[str] = None
    provider_title: Optional[str] = None
    reason_question: Optional[str] = None
    language: Optional[str] = None


def _voice_or_create(db: Session, clinic_id: str) -> ClinicAiVoice:
    row = db.query(ClinicAiVoice).filter(ClinicAiVoice.clinic_id == clinic_id).first()
    if row is None:
        row = ClinicAiVoice(clinic_id=clinic_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/voice", response_model=VoiceOut)
def get_voice(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = _voice_or_create(db, clinic.id)
    data = {
        "assistant_name": row.assistant_name,
        "provider_title": row.provider_title,
        "reason_question": row.reason_question,
        "language": row.language,
    }
    etag = add_cache_headers(response, data)
    if check_etag(request, etag):
        return Response(status_code=304)
    return VoiceOut(**data)


@router.put("/voice", response_model=VoiceOut)
def put_voice(
    body: VoicePatch,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = _voice_or_create(db, clinic.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return VoiceOut(
        assistant_name=row.assistant_name,
        provider_title=row.provider_title,
        reason_question=row.reason_question,
        language=row.language,
    )


# ---------------------------------------------------------------------------
# AI disclosure
# ---------------------------------------------------------------------------

class DisclosureOut(BaseModel):
    required: bool
    phrase: str
    last_reviewed_at: Optional[str]


class DisclosurePatch(BaseModel):
    required: Optional[bool] = None
    phrase: Optional[str] = None


def _disclosure_or_create(db: Session, clinic_id: str) -> ClinicAiDisclosure:
    row = db.query(ClinicAiDisclosure).filter(ClinicAiDisclosure.clinic_id == clinic_id).first()
    if row is None:
        row = ClinicAiDisclosure(clinic_id=clinic_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _disclosure_to_out(row: ClinicAiDisclosure) -> DisclosureOut:
    return DisclosureOut(
        required=row.required,
        phrase=row.phrase or "",
        last_reviewed_at=row.last_reviewed_at.isoformat() if row.last_reviewed_at else None,
    )


@router.get("/disclosure", response_model=DisclosureOut)
def get_disclosure(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    return _disclosure_to_out(_disclosure_or_create(db, clinic.id))


@router.put("/disclosure", response_model=DisclosureOut)
def put_disclosure(
    body: DisclosurePatch,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = _disclosure_or_create(db, clinic.id)
    updates = body.model_dump(exclude_unset=True)
    if "phrase" in updates and updates["phrase"] != row.phrase:
        row.last_reviewed_at = datetime.utcnow()
    for field, value in updates.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _disclosure_to_out(row)


# ---------------------------------------------------------------------------
# Services bookable
# ---------------------------------------------------------------------------

class ServiceBookableOut(BaseModel):
    service_id: int
    name: str
    duration_min: Optional[int]
    base_price: Optional[float]
    bookable: bool


class ServiceBookablePatch(BaseModel):
    bookable: bool


@router.get("/services-bookable", response_model=List[ServiceBookableOut])
def list_services_bookable(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    services = (
        db.query(Service)
        .filter(Service.clinic_id == clinic.id)
        .order_by(Service.id)
        .all()
    )
    flag_rows = (
        db.query(ServiceAiBookable)
        .filter(ServiceAiBookable.clinic_id == clinic.id)
        .all()
    )
    flag_by_id = {f.service_id: f.bookable for f in flag_rows}
    out: List[ServiceBookableOut] = []
    for s in services:
        out.append(ServiceBookableOut(
            service_id=s.id,
            name=s.name,
            duration_min=s.duration_min,
            base_price=float(s.base_price) if s.base_price is not None else None,
            bookable=bool(flag_by_id.get(s.id, False)),
        ))
    return out


@router.put("/services-bookable/{service_id}", response_model=ServiceBookableOut)
def put_service_bookable(
    service_id: int,
    body: ServiceBookablePatch,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    svc = (
        db.query(Service)
        .filter(Service.id == service_id, Service.clinic_id == clinic.id)
        .first()
    )
    if svc is None:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found in clinic {clinic.id}")

    flag = (
        db.query(ServiceAiBookable)
        .filter(ServiceAiBookable.service_id == service_id)
        .first()
    )
    if flag is None:
        flag = ServiceAiBookable(service_id=service_id, clinic_id=clinic.id, bookable=body.bookable)
        db.add(flag)
    else:
        flag.bookable = body.bookable
    db.commit()
    db.refresh(flag)

    return ServiceBookableOut(
        service_id=svc.id,
        name=svc.name,
        duration_min=svc.duration_min,
        base_price=float(svc.base_price) if svc.base_price is not None else None,
        bookable=flag.bookable,
    )


# ---------------------------------------------------------------------------
# Knowledge docs
# ---------------------------------------------------------------------------

class KnowledgeListItem(BaseModel):
    filename: str
    title: str
    word_count: int
    updated_at: Optional[str]


class KnowledgeDoc(BaseModel):
    filename: str
    title: str
    body: str
    word_count: int
    updated_at: Optional[str]


class KnowledgeCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=400)
    body: str = ""


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


_WORD_RE = re.compile(r"\b\w+\b")


def _word_count(body: str) -> int:
    """Count alphanumeric word tokens — markdown punctuation like '#' or '*' is skipped."""
    return len(_WORD_RE.findall(body))


def _doc_to_full(row: ClinicKnowledgeDoc) -> KnowledgeDoc:
    return KnowledgeDoc(
        filename=row.filename,
        title=row.title,
        body=row.body or "",
        word_count=row.word_count,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@router.get("/knowledge", response_model=List[KnowledgeListItem])
def list_knowledge(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    rows = (
        db.query(ClinicKnowledgeDoc)
        .filter(ClinicKnowledgeDoc.clinic_id == clinic.id)
        .order_by(ClinicKnowledgeDoc.filename)
        .all()
    )
    return [
        KnowledgeListItem(
            filename=r.filename,
            title=r.title,
            word_count=r.word_count,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in rows
    ]


@router.get("/knowledge/{filename}", response_model=KnowledgeDoc)
def get_knowledge(
    filename: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = (
        db.query(ClinicKnowledgeDoc)
        .filter(
            ClinicKnowledgeDoc.clinic_id == clinic.id,
            ClinicKnowledgeDoc.filename == filename,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Knowledge doc {filename} not found")
    return _doc_to_full(row)


@router.post("/knowledge", response_model=KnowledgeDoc, status_code=201)
def create_knowledge(
    body: KnowledgeCreate,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    existing = (
        db.query(ClinicKnowledgeDoc)
        .filter(
            ClinicKnowledgeDoc.clinic_id == clinic.id,
            ClinicKnowledgeDoc.filename == body.filename,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Knowledge doc {body.filename!r} already exists for this clinic",
        )
    row = ClinicKnowledgeDoc(
        clinic_id=clinic.id,
        filename=body.filename,
        title=body.title,
        body=body.body,
        word_count=_word_count(body.body),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _doc_to_full(row)


@router.put("/knowledge/{filename}", response_model=KnowledgeDoc)
def update_knowledge(
    filename: str,
    body: KnowledgeUpdate,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = (
        db.query(ClinicKnowledgeDoc)
        .filter(
            ClinicKnowledgeDoc.clinic_id == clinic.id,
            ClinicKnowledgeDoc.filename == filename,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Knowledge doc {filename} not found")
    updates = body.model_dump(exclude_unset=True)
    if "title" in updates:
        row.title = updates["title"]
    if "body" in updates:
        row.body = updates["body"]
        row.word_count = _word_count(updates["body"])
    db.commit()
    db.refresh(row)
    return _doc_to_full(row)


@router.delete("/knowledge/{filename}", status_code=204)
def delete_knowledge(
    filename: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    row = (
        db.query(ClinicKnowledgeDoc)
        .filter(
            ClinicKnowledgeDoc.clinic_id == clinic.id,
            ClinicKnowledgeDoc.filename == filename,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Knowledge doc {filename} not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)

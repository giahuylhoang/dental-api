"""Clinical router: patient extensions, clinical notes, denture cases."""
import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Patient
from database.clinical.models import (
    PatientMedicalHistory, PatientInsurance, PatientConsent, Document,
    ClinicalNote, DentureCase, DentureCaseEvent, PatientNote,
)
from database.v1_1.models import ToothChartEntry, DentureCaseImplant
from database.v1_1.lifecycle import (
    get_status, set_status, promote_if_complete, PATIENT_STATUSES,
)
from api.dependencies import get_authorized_clinic
from services.storage import get_storage_backend

router = APIRouter(prefix="/api/v2/clinical", tags=["clinical"])


# ---------------------------------------------------------------------------
# Quick-book / lifecycle (v1.1)
# ---------------------------------------------------------------------------

class QuickBookIn(BaseModel):
    """Minimum data set for a phone-booking patient: name + phone."""
    name: str                        # full or "first last"; we split on first space
    phone: str
    source: Optional[str] = None     # how they found the clinic
    notes: Optional[str] = None


class QuickBookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: str
    status: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_new: bool


class PatientStatusOut(BaseModel):
    patient_id: str
    status: str


class PatientStatusIn(BaseModel):
    status: str
    notes: Optional[str] = None


def _split_name(full: str) -> tuple[str, Optional[str]]:
    parts = full.strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


@router.post("/patients/quick-book", response_model=QuickBookOut, status_code=200)
def quick_book_patient(
    body: QuickBookIn,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Create (or reuse) a phone-booking patient with status='pending'.

    Idempotent on (clinic_id, phone): if a patient with that phone already
    exists in this clinic, return them as-is — no duplicate row, no status
    change. The caller can later POST consent/insurance/dob and the lifecycle
    auto-promotes to 'active' via `promote_if_complete`.
    """
    phone_clean = "".join(c for c in body.phone if c.isdigit() or c == "+")
    if not phone_clean:
        raise HTTPException(status_code=422, detail="phone is required")

    existing = (
        db.query(Patient)
        .filter(Patient.clinic_id == clinic.id, Patient.phone == phone_clean)
        .first()
    )
    if existing is not None:
        return QuickBookOut(
            patient_id=existing.id,
            status=get_status(db, existing.id),
            first_name=existing.first_name,
            last_name=existing.last_name,
            phone=existing.phone,
            is_new=False,
        )

    first, last = _split_name(body.name)
    patient = Patient(
        clinic_id=clinic.id,
        first_name=first,
        last_name=last,
        phone=phone_clean,
    )
    db.add(patient)
    db.flush()

    set_status(
        db, patient.id, clinic.id, "pending",
        notes=body.notes or (f"quick-book; source={body.source}" if body.source else "quick-book"),
    )
    db.commit()
    db.refresh(patient)
    return QuickBookOut(
        patient_id=patient.id,
        status="pending",
        first_name=patient.first_name,
        last_name=patient.last_name,
        phone=patient.phone,
        is_new=True,
    )


@router.get("/patients/{patient_id}/status", response_model=PatientStatusOut)
def get_patient_status(
    patient_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientStatusOut(patient_id=p.id, status=get_status(db, p.id))


@router.post("/patients/{patient_id}/status", response_model=PatientStatusOut)
def set_patient_status(
    patient_id: str,
    body: PatientStatusIn,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    if body.status not in PATIENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"invalid status; expected one of {list(PATIENT_STATUSES)}")
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    set_status(db, p.id, clinic.id, body.status, notes=body.notes)
    db.commit()
    return PatientStatusOut(patient_id=p.id, status=body.status)


@router.post("/patients/{patient_id}/promote", response_model=PatientStatusOut)
def promote_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Auto-promote pending → active if all required fields are now present."""
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    final = promote_if_complete(db, p)
    db.commit()
    return PatientStatusOut(patient_id=p.id, status=final)

# ---------------------------------------------------------------------------
# Stage machine
# ---------------------------------------------------------------------------
STAGE_ORDER = ["consult", "prelim_imp", "final_imp", "bite_reg", "wax_tryin", "insert", "adjust", "complete"]


def _next_stages(current: str) -> List[str]:
    """Return the single valid next stage (no skipping)."""
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        return []
    if idx + 1 < len(STAGE_ORDER):
        return [STAGE_ORDER[idx + 1]]
    return []


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class MedicalHistoryIn(BaseModel):
    conditions: Optional[list] = []
    bisphosphonates_use: Optional[bool] = False
    allergies_text: Optional[str] = None


class MedicalHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    conditions: Optional[list] = []
    bisphosphonates_use: Optional[bool] = False
    allergies_text: Optional[str] = None


class InsuranceIn(BaseModel):
    carrier: str
    policy_number: Optional[str] = None
    group_number: Optional[str] = None
    holder_name: Optional[str] = None
    holder_relationship: Optional[str] = None
    assignment_of_benefits: Optional[bool] = False
    coverage_pct_by_category: Optional[dict] = {}
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_primary: Optional[bool] = False


class InsuranceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    carrier: str
    policy_number: Optional[str] = None
    group_number: Optional[str] = None
    holder_name: Optional[str] = None
    holder_relationship: Optional[str] = None
    assignment_of_benefits: Optional[bool] = False
    coverage_pct_by_category: Optional[dict] = {}
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_primary: Optional[bool] = False


class ConsentIn(BaseModel):
    form_kind: str
    form_version: Optional[str] = None
    signed_at: Optional[datetime] = None
    signature_blob_url: Optional[str] = None
    witness_name: Optional[str] = None


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    form_kind: str
    form_version: Optional[str] = None
    signed_at: Optional[datetime] = None
    signature_blob_url: Optional[str] = None
    witness_name: Optional[str] = None


class DocumentIn(BaseModel):
    kind: str
    storage_url: str
    content_sha256: str
    mime: Optional[str] = None
    size_bytes: Optional[int] = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    kind: str
    storage_url: str
    storage_backend: Optional[str] = None
    original_name: Optional[str] = None
    content_sha256: str
    mime: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None


ALLOWED_DOC_MIME = {"image/jpeg", "image/png", "image/heic", "application/pdf"}
MAX_DOC_BYTES = 25 * 1024 * 1024  # 25 MB

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/heic": ".heic",
    "application/pdf": ".pdf",
}


class DocUploadRequestIn(BaseModel):
    filename: str
    mime: str
    size_bytes: int
    kind: str = "other"


class DocUploadTicketOut(BaseModel):
    upload_url: str
    storage_key: str
    storage_backend: str


class DocCompleteIn(BaseModel):
    storage_key: str
    kind: str = "other"
    original_name: Optional[str] = None
    uploaded_by: Optional[str] = None


class DocDownloadOut(BaseModel):
    download_url: str


class NoteIn(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    author_id: Optional[str] = None
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None


class NotePatch(BaseModel):
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    appointment_id: Optional[str] = None
    author_id: Optional[str] = None
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None
    locked_at: Optional[datetime] = None
    supersedes_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DentureCaseIn(BaseModel):
    patient_id: str
    arch: str
    case_type: str
    notes: Optional[str] = None


class DentureCaseAdvance(BaseModel):
    stage: str
    note: Optional[str] = None
    photo_document_ids: Optional[list] = []
    provider_id: Optional[str] = None


class DentureCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    arch: str
    case_type: str
    current_stage: str
    status: str
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None


class PatientNoteIn(BaseModel):
    body: str
    author_id: Optional[str] = None


class PatientNotePatch(BaseModel):
    body: str


class PatientNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinic_id: str
    patient_id: str
    author_id: Optional[str] = None
    body: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_patient(patient_id: str, clinic: Clinic, db: Session) -> Patient:
    p = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.clinic_id == clinic.id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


def _get_denture_case(case_id: str, clinic: Clinic, db: Session) -> DentureCase:
    c = db.query(DentureCase).filter(
        DentureCase.id == case_id,
        DentureCase.clinic_id == clinic.id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Denture case not found")
    return c


# ---------------------------------------------------------------------------
# Patient extensions
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/medical-history", response_model=Optional[MedicalHistoryOut])
def get_medical_history(patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientMedicalHistory).filter(
        PatientMedicalHistory.patient_id == patient_id,
        PatientMedicalHistory.clinic_id == clinic.id,
    ).first()


@router.post("/patients/{patient_id}/medical-history", response_model=MedicalHistoryOut)
def upsert_medical_history(patient_id: str, body: MedicalHistoryIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    existing = db.query(PatientMedicalHistory).filter(
        PatientMedicalHistory.patient_id == patient_id,
        PatientMedicalHistory.clinic_id == clinic.id,
    ).first()
    if existing:
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    obj = PatientMedicalHistory(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/insurance", response_model=List[InsuranceOut])
def list_insurance(patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientInsurance).filter(
        PatientInsurance.patient_id == patient_id,
        PatientInsurance.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/insurance", response_model=InsuranceOut, status_code=201)
def add_insurance(patient_id: str, body: InsuranceIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    obj = PatientInsurance(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/consents", response_model=List[ConsentOut])
def list_consents(patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientConsent).filter(
        PatientConsent.patient_id == patient_id,
        PatientConsent.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/consents", response_model=ConsentOut, status_code=201)
def add_consent(patient_id: str, body: ConsentIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    obj = PatientConsent(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/documents", response_model=List[DocumentOut])
def list_documents(patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(Document).filter(
        Document.patient_id == patient_id,
        Document.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/documents", response_model=DocumentOut, status_code=201, deprecated=True)
def add_document(patient_id: str, body: DocumentIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    # Deprecated: trusted client-supplied metadata. Use request-upload → complete instead.
    raise HTTPException(status_code=410, detail="Use documents/request-upload then documents/complete")


@router.post("/patients/{patient_id}/documents/request-upload", response_model=DocUploadTicketOut)
def request_document_upload(patient_id: str, body: DocUploadRequestIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    if body.mime not in ALLOWED_DOC_MIME:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    if body.size_bytes <= 0 or body.size_bytes > MAX_DOC_BYTES:
        raise HTTPException(status_code=400, detail="File too large")
    ext = _EXT_BY_MIME.get(body.mime, Path(body.filename).suffix or "")
    storage_key = f"{clinic.id}/patients/{patient_id}/{uuid.uuid4().hex}{ext}"
    storage = get_storage_backend()
    upload_url = storage.signed_put_url(storage_key, content_type=body.mime, max_bytes=body.size_bytes)
    backend_name = "gcs" if os.getenv("GCS_BUCKET", "").strip() else "local"
    return DocUploadTicketOut(upload_url=upload_url, storage_key=storage_key, storage_backend=backend_name)


@router.post("/patients/{patient_id}/documents/complete", response_model=DocumentOut, status_code=201)
def complete_document_upload(patient_id: str, body: DocCompleteIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    prefix = f"{clinic.id}/patients/{patient_id}/"
    if not body.storage_key.startswith(prefix):
        raise HTTPException(status_code=400, detail="storage_key outside patient prefix")

    storage = get_storage_backend()
    info = storage.stat(body.storage_key)
    if info is None:
        raise HTTPException(status_code=400, detail="Uploaded object not found")

    size = int(info["size"])
    if size <= 0 or size > MAX_DOC_BYTES:
        storage.delete(body.storage_key)
        raise HTTPException(status_code=400, detail="File too large")

    data = storage.read_bytes(body.storage_key)
    sha = hashlib.sha256(data).hexdigest()
    mime = info.get("content_type")
    if mime is not None and mime not in ALLOWED_DOC_MIME:
        storage.delete(body.storage_key)
        raise HTTPException(status_code=400, detail="Unsupported file type")

    backend_name = "gcs" if os.getenv("GCS_BUCKET", "").strip() else "local"

    existing = db.query(Document).filter(
        Document.clinic_id == clinic.id,
        Document.patient_id == patient_id,
        Document.content_sha256 == sha,
    ).first()
    if existing:
        storage.delete(body.storage_key)  # new bytes duplicate an existing doc; don't leak them
        return existing

    doc = Document(
        clinic_id=clinic.id,
        patient_id=patient_id,
        kind=body.kind,
        storage_url=body.storage_key,
        storage_backend=backend_name,
        original_name=body.original_name,
        content_sha256=sha,
        mime=mime,
        size_bytes=size,
        uploaded_by=body.uploaded_by,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documents/{document_id}/download", response_model=DocDownloadOut)
def get_document_download_url(document_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.clinic_id == clinic.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    url = get_storage_backend().signed_get_url(doc.storage_url)
    return DocDownloadOut(download_url=url)


# ---------------------------------------------------------------------------
# Clinical notes
# ---------------------------------------------------------------------------

@router.post("/notes", response_model=NoteOut, status_code=201)
def create_note(body: NoteIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(body.patient_id, clinic, db)
    obj = ClinicalNote(clinic_id=clinic.id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/notes/{note_id}", response_model=NoteOut)
def patch_note(note_id: str, body: NotePatch, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    note = db.query(ClinicalNote).filter(
        ClinicalNote.id == note_id,
        ClinicalNote.clinic_id == clinic.id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.locked_at is not None:
        raise HTTPException(status_code=409, detail="Note is locked")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(note, k, v)
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.post("/notes/{note_id}/lock", response_model=NoteOut)
def lock_note(note_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    note = db.query(ClinicalNote).filter(
        ClinicalNote.id == note_id,
        ClinicalNote.clinic_id == clinic.id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.locked_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.post("/notes/{note_id}/amend", response_model=NoteOut, status_code=201)
def amend_note(note_id: str, body: NotePatch, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    original = db.query(ClinicalNote).filter(
        ClinicalNote.id == note_id,
        ClinicalNote.clinic_id == clinic.id,
    ).first()
    if not original:
        raise HTTPException(status_code=404, detail="Note not found")
    # Create amendment with supersedes_id pointing to original
    new_note = ClinicalNote(
        clinic_id=original.clinic_id,
        patient_id=original.patient_id,
        appointment_id=original.appointment_id,
        author_id=original.author_id,
        soap_subjective=original.soap_subjective,
        soap_objective=original.soap_objective,
        soap_assessment=original.soap_assessment,
        soap_plan=original.soap_plan,
        supersedes_id=original.id,
    )
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(new_note, k, v)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@router.get("/notes", response_model=List[NoteOut])
def list_notes(patient_id: Optional[str] = None, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    q = db.query(ClinicalNote).filter(ClinicalNote.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(ClinicalNote.patient_id == patient_id)
    return q.all()


# ---------------------------------------------------------------------------
# Patient CRM notes (lightweight, editable, append-style)
# ---------------------------------------------------------------------------

@router.post("/patients/{patient_id}/notes", response_model=PatientNoteOut, status_code=201)
def create_patient_note(patient_id: str, body: PatientNoteIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    obj = PatientNote(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/notes", response_model=List[PatientNoteOut])
def list_patient_notes(patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientNote).filter(
        PatientNote.patient_id == patient_id,
        PatientNote.clinic_id == clinic.id,
    ).order_by(PatientNote.created_at.desc(), PatientNote.id.desc()).all()


@router.patch("/patient-notes/{note_id}", response_model=PatientNoteOut)
def patch_patient_note(note_id: str, body: PatientNotePatch, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    note = db.query(PatientNote).filter(
        PatientNote.id == note_id,
        PatientNote.clinic_id == clinic.id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.body = body.body
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.delete("/patient-notes/{note_id}", status_code=204)
def delete_patient_note(note_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    note = db.query(PatientNote).filter(
        PatientNote.id == note_id,
        PatientNote.clinic_id == clinic.id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Denture cases
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/denture-cases", response_model=List[DentureCaseOut])
def list_denture_cases_for_patient(
    patient_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)
):
    _get_patient(patient_id, clinic, db)
    return (
        db.query(DentureCase)
        .filter(DentureCase.clinic_id == clinic.id, DentureCase.patient_id == patient_id)
        .order_by(DentureCase.opened_at.desc())
        .all()
    )


@router.post("/denture-cases", response_model=DentureCaseOut, status_code=201)
def create_denture_case(body: DentureCaseIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    _get_patient(body.patient_id, clinic, db)
    obj = DentureCase(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        arch=body.arch,
        case_type=body.case_type,
        notes=body.notes,
        current_stage="consult",
        status="open",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/denture-cases/{case_id}", response_model=DentureCaseOut)
def get_denture_case(case_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    return _get_denture_case(case_id, clinic, db)


@router.post("/denture-cases/{case_id}/advance", response_model=DentureCaseOut)
def advance_denture_case(case_id: str, body: DentureCaseAdvance, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    case = _get_denture_case(case_id, clinic, db)
    if case.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot advance a closed case")
    valid = _next_stages(case.current_stage)
    if body.stage not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid stage transition: {case.current_stage} -> {body.stage}. Valid: {valid}")
    event = DentureCaseEvent(
        case_id=case.id,
        stage=body.stage,
        provider_id=body.provider_id,
        note=body.note,
        photo_document_ids=body.photo_document_ids or [],
    )
    db.add(event)
    case.current_stage = body.stage
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case


@router.post("/denture-cases/{case_id}/close", response_model=DentureCaseOut)
def close_denture_case(case_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    case = _get_denture_case(case_id, clinic, db)
    case.status = "closed"
    case.closed_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case


@router.get("/denture-cases", response_model=List[DentureCaseOut])
def list_denture_cases(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(DentureCase).filter(DentureCase.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(DentureCase.patient_id == patient_id)
    if status:
        q = q.filter(DentureCase.status == status)
    if stage:
        q = q.filter(DentureCase.current_stage == stage)
    return q.all()


# ---------------------------------------------------------------------------
# Document upload (multipart)
# ---------------------------------------------------------------------------

class DocumentUploadOut(BaseModel):
    id: str
    storage_url: str
    sha256: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    kind: str
    patient_id: str
    deduped: bool


@router.post("/documents/upload", response_model=DocumentUploadOut)
def upload_document(
    file: UploadFile = File(...),
    kind: str = Form(...),
    patient_id: str = Form(...),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_patient(patient_id, clinic, db)
    data = file.file.read()
    sha256 = hashlib.sha256(data).hexdigest()

    existing = db.query(Document).filter(
        Document.clinic_id == clinic.id,
        Document.content_sha256 == sha256,
    ).first()
    if existing:
        return DocumentUploadOut(
            id=existing.id,
            storage_url=existing.storage_url,
            sha256=existing.content_sha256,
            mime_type=existing.mime,
            size_bytes=existing.size_bytes,
            kind=existing.kind,
            patient_id=existing.patient_id,
            deduped=True,
        )

    ext = Path(file.filename).suffix if file.filename else ""
    rel_path = f"var/uploads/{clinic.id}/{sha256[:2]}/{sha256}{ext}"
    abs_path = Path(rel_path)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(data)

    doc = Document(
        clinic_id=clinic.id,
        patient_id=patient_id,
        kind=kind,
        storage_url=rel_path,
        content_sha256=sha256,
        mime=file.content_type,
        size_bytes=len(data),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentUploadOut(
        id=doc.id,
        storage_url=doc.storage_url,
        sha256=doc.content_sha256,
        mime_type=doc.mime,
        size_bytes=doc.size_bytes,
        kind=doc.kind,
        patient_id=doc.patient_id,
        deduped=False,
    )


# ---------------------------------------------------------------------------
# Tooth chart
# ---------------------------------------------------------------------------

class ToothChartEntryOut(BaseModel):
    tooth_number: int
    status: str
    surface_notes: Optional[dict] = None


class ToothChartEntryIn(BaseModel):
    tooth_number: int
    status: str
    surface_notes: Optional[dict] = None


def _build_tooth_chart(rows: list) -> List[ToothChartEntryOut]:
    by_tooth = {r.tooth_number: r for r in rows}
    result = []
    for n in range(1, 33):
        if n in by_tooth:
            r = by_tooth[n]
            result.append(ToothChartEntryOut(
                tooth_number=r.tooth_number,
                status=r.status,
                surface_notes=r.surface_notes,
            ))
        else:
            result.append(ToothChartEntryOut(tooth_number=n, status="present", surface_notes=None))
    return result


@router.get("/patients/{patient_id}/tooth-chart", response_model=List[ToothChartEntryOut])
def get_tooth_chart(
    patient_id: str,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_patient(patient_id, clinic, db)
    rows = db.query(ToothChartEntry).filter(
        ToothChartEntry.clinic_id == clinic.id,
        ToothChartEntry.patient_id == patient_id,
    ).all()
    return _build_tooth_chart(rows)


@router.post("/patients/{patient_id}/tooth-chart", response_model=List[ToothChartEntryOut])
def upsert_tooth_chart(
    patient_id: str,
    body: List[ToothChartEntryIn],
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_patient(patient_id, clinic, db)
    now = datetime.utcnow()
    for entry in body:
        existing = db.query(ToothChartEntry).filter(
            ToothChartEntry.clinic_id == clinic.id,
            ToothChartEntry.patient_id == patient_id,
            ToothChartEntry.tooth_number == entry.tooth_number,
        ).first()
        if existing:
            existing.status = entry.status
            if entry.surface_notes is not None:
                existing.surface_notes = entry.surface_notes
            existing.last_examined_at = now
            existing.updated_at = now
        else:
            db.add(ToothChartEntry(
                clinic_id=clinic.id,
                patient_id=patient_id,
                tooth_number=entry.tooth_number,
                status=entry.status,
                surface_notes=entry.surface_notes,
                last_examined_at=now,
            ))
    db.commit()
    rows = db.query(ToothChartEntry).filter(
        ToothChartEntry.clinic_id == clinic.id,
        ToothChartEntry.patient_id == patient_id,
    ).all()
    return _build_tooth_chart(rows)


# ---------------------------------------------------------------------------
# Insurance PUT / DELETE
# ---------------------------------------------------------------------------

@router.put("/patients/{patient_id}/insurance/{insurance_id}", response_model=InsuranceOut)
def update_insurance(
    patient_id: str,
    insurance_id: str,
    body: InsuranceIn,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_patient(patient_id, clinic, db)
    obj = db.query(PatientInsurance).filter(
        PatientInsurance.id == insurance_id,
        PatientInsurance.patient_id == patient_id,
        PatientInsurance.clinic_id == clinic.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Insurance not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/patients/{patient_id}/insurance/{insurance_id}", status_code=204)
def delete_insurance(
    patient_id: str,
    insurance_id: str,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_patient(patient_id, clinic, db)
    obj = db.query(PatientInsurance).filter(
        PatientInsurance.id == insurance_id,
        PatientInsurance.patient_id == patient_id,
        PatientInsurance.clinic_id == clinic.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Insurance not found")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# Denture case implants
# ---------------------------------------------------------------------------

class ImplantIn(BaseModel):
    tooth_position: int
    vendor: str
    model: Optional[str] = None
    lot_number: str
    surface_treatment: Optional[str] = None
    abutment_type: Optional[str] = None
    placed_date: Optional[str] = None


class ImplantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    denture_case_id: str
    tooth_position: int
    vendor: str
    model: Optional[str] = None
    lot_number: str
    surface_treatment: Optional[str] = None
    abutment_type: Optional[str] = None
    placed_date: Optional[str] = None


@router.get("/denture-cases/{case_id}/implants", response_model=List[ImplantOut])
def list_implants(
    case_id: str,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_denture_case(case_id, clinic, db)
    return db.query(DentureCaseImplant).filter(
        DentureCaseImplant.denture_case_id == case_id,
    ).all()


@router.post("/denture-cases/{case_id}/implants", response_model=ImplantOut, status_code=201)
def create_implant(
    case_id: str,
    body: ImplantIn,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    _get_denture_case(case_id, clinic, db)
    from datetime import date as _date
    placed = None
    if body.placed_date:
        placed = _date.fromisoformat(body.placed_date)
    obj = DentureCaseImplant(
        denture_case_id=case_id,
        tooth_position=body.tooth_position,
        vendor=body.vendor,
        model=body.model,
        lot_number=body.lot_number,
        surface_treatment=body.surface_treatment,
        abutment_type=body.abutment_type,
        placed_date=placed,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Appointments (v2 — includes chief_complaint)
# ---------------------------------------------------------------------------

from database.models import Appointment


@router.get("/appointments/{appointment_id}")
def get_appointment_v2(
    appointment_id: str,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == clinic.id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {
        "id": appt.id,
        "patient_id": appt.patient_id,
        "provider_id": appt.provider_id,
        "service_id": appt.service_id,
        "start_time": appt.start_time.isoformat(),
        "end_time": appt.end_time.isoformat(),
        "reason_note": appt.reason_note,
        "chief_complaint": appt.chief_complaint,
        "status": appt.status.value if hasattr(appt.status, "value") else appt.status,
    }

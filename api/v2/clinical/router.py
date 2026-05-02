"""Clinical router: patient extensions, clinical notes, denture cases."""
import os
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Patient
from database.clinical.models import (
    PatientMedicalHistory, PatientInsurance, PatientConsent, Document,
    ClinicalNote, DentureCase, DentureCaseEvent,
)
from database.v1_1.lifecycle import (
    get_status, set_status, promote_if_complete, PATIENT_STATUSES,
)
from api.main import get_clinic

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
    clinic: Clinic = Depends(get_clinic),
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
    clinic: Clinic = Depends(get_clinic),
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
    clinic: Clinic = Depends(get_clinic),
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
    clinic: Clinic = Depends(get_clinic),
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
    content_sha256: str
    mime: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None


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
def get_medical_history(patient_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientMedicalHistory).filter(
        PatientMedicalHistory.patient_id == patient_id,
        PatientMedicalHistory.clinic_id == clinic.id,
    ).first()


@router.post("/patients/{patient_id}/medical-history", response_model=MedicalHistoryOut)
def upsert_medical_history(patient_id: str, body: MedicalHistoryIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def list_insurance(patient_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientInsurance).filter(
        PatientInsurance.patient_id == patient_id,
        PatientInsurance.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/insurance", response_model=InsuranceOut, status_code=201)
def add_insurance(patient_id: str, body: InsuranceIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    obj = PatientInsurance(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/consents", response_model=List[ConsentOut])
def list_consents(patient_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(PatientConsent).filter(
        PatientConsent.patient_id == patient_id,
        PatientConsent.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/consents", response_model=ConsentOut, status_code=201)
def add_consent(patient_id: str, body: ConsentIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    obj = PatientConsent(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/patients/{patient_id}/documents", response_model=List[DocumentOut])
def list_documents(patient_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    return db.query(Document).filter(
        Document.patient_id == patient_id,
        Document.clinic_id == clinic.id,
    ).all()


@router.post("/patients/{patient_id}/documents", response_model=DocumentOut, status_code=201)
def add_document(patient_id: str, body: DocumentIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(patient_id, clinic, db)
    # Dedup on sha256
    existing = db.query(Document).filter(
        Document.clinic_id == clinic.id,
        Document.content_sha256 == body.content_sha256,
    ).first()
    if existing:
        return existing
    obj = Document(clinic_id=clinic.id, patient_id=patient_id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Clinical notes
# ---------------------------------------------------------------------------

@router.post("/notes", response_model=NoteOut, status_code=201)
def create_note(body: NoteIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    _get_patient(body.patient_id, clinic, db)
    obj = ClinicalNote(clinic_id=clinic.id, **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/notes/{note_id}", response_model=NoteOut)
def patch_note(note_id: str, body: NotePatch, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def lock_note(note_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def amend_note(note_id: str, body: NotePatch, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def list_notes(patient_id: Optional[str] = None, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    q = db.query(ClinicalNote).filter(ClinicalNote.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(ClinicalNote.patient_id == patient_id)
    return q.all()


# ---------------------------------------------------------------------------
# Denture cases
# ---------------------------------------------------------------------------

@router.post("/denture-cases", response_model=DentureCaseOut, status_code=201)
def create_denture_case(body: DentureCaseIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def get_denture_case(case_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return _get_denture_case(case_id, clinic, db)


@router.post("/denture-cases/{case_id}/advance", response_model=DentureCaseOut)
def advance_denture_case(case_id: str, body: DentureCaseAdvance, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
def close_denture_case(case_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
    clinic: Clinic = Depends(get_clinic),
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

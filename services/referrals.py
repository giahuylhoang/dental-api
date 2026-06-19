"""Referral business logic: create (mint upload tickets) + complete (verify + notify).

Follows the holds.py convention: services do the work and FLUSH, the router commits.
Storage is the pluggable backend (GCS in prod, Local in dev/tests).
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from database.models import Clinic, Provider, Referral, ReferralDocument, ReferralStatus
from api.v1.public_referrals.schemas import (
    ALLOWED_MIME,
    MAX_FILE_BYTES,
    MAX_FILES,
    ReferralCreateRequest,
    UploadTicket,
)

logger = logging.getLogger(__name__)


def _kind_for_mime(mime: str) -> str:
    if mime == "application/pdf":
        return "pdf"
    if mime.startswith("image/"):
        return "xray"
    return "other"


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


def _safe_ext(name: str) -> str:
    ext = Path(name or "").suffix
    # keep it short + harmless
    return ext if (0 < len(ext) <= 8 and ext.replace(".", "").isalnum()) else ""


def create_referral(
    db: Session,
    *,
    clinic: Clinic,
    payload: ReferralCreateRequest,
    submit_ip: Optional[str],
    storage,
) -> Tuple[Referral, List[UploadTicket]]:
    """Validate the manifest, create the Referral + pending ReferralDocument rows,
    and return one signed PUT ticket per file. Does NOT commit (caller commits)."""
    files = payload.files or []
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=422, detail=f"too_many_files:max_{MAX_FILES}")
    for f in files:
        if f.mime not in ALLOWED_MIME:
            raise HTTPException(status_code=422, detail=f"unsupported_type:{f.mime}")
        if (f.size or 0) > MAX_FILE_BYTES:
            raise HTTPException(status_code=422, detail="file_too_large")

    referral = Referral(
        clinic_id=clinic.id,
        patient_name=payload.patient_name.strip(),
        patient_phone=payload.patient_phone.strip(),
        referred_by=payload.referred_by.strip(),
        referrer_contact=(payload.referrer_contact or "").strip() or None,
        proposed_extraction_date=_parse_date(payload.proposed_extraction_date),
        tx_plan=(payload.tx_plan or "").strip() or None,
        provider_id=payload.provider_id,
        status=ReferralStatus.NEW,
        source="public-referral",
        submit_ip=submit_ip,
    )
    db.add(referral)
    db.flush()  # assign referral.id

    backend_name = "local" if storage.__class__.__name__ == "LocalBackend" else "gcs"
    tickets: List[UploadTicket] = []
    for idx, f in enumerate(files):
        object_key = f"{clinic.id}/referrals/{referral.id}/{uuid.uuid4().hex}{_safe_ext(f.name)}"
        db.add(ReferralDocument(
            clinic_id=clinic.id,
            referral_id=referral.id,
            kind=_kind_for_mime(f.mime),
            storage_url=object_key,
            storage_backend=backend_name,
            mime=f.mime,
            size_bytes=f.size,          # claimed; re-verified on complete
            original_name=f.name,
        ))
        tickets.append(UploadTicket(
            file_index=idx,
            object_key=object_key,
            put_url=storage.signed_put_url(object_key, f.mime, MAX_FILE_BYTES),
            content_type=f.mime,
        ))
    db.flush()
    return referral, tickets


def _provider_label(db: Session, clinic: Clinic, provider_id: Optional[int]) -> str:
    if provider_id is None:
        return "Either / first available"
    p = db.query(Provider).filter(
        Provider.id == provider_id, Provider.clinic_id == clinic.id
    ).first()
    if not p:
        return "Either / first available"
    return " ".join(filter(None, [p.title, p.name])).strip() or p.name


def complete_referral(
    db: Session,
    background_tasks: BackgroundTasks,
    *,
    clinic: Clinic,
    referral_id: str,
    storage,
) -> Referral:
    """Reconcile uploaded objects against the pending document rows (authoritative:
    keep rows whose object actually exists + is within size; delete the rest), mark
    READY, and schedule the clinic notification email. Commits."""
    referral = db.query(Referral).filter(
        Referral.id == referral_id, Referral.clinic_id == clinic.id
    ).first()
    if referral is None:
        raise HTTPException(status_code=404, detail="referral_not_found")

    prefix = f"{clinic.id}/referrals/{referral.id}/"
    kept: List[ReferralDocument] = []
    for doc in list(referral.documents):
        # Defensive: object key must belong to THIS referral.
        if not doc.storage_url.startswith(prefix):
            db.delete(doc)
            continue
        st = storage.stat(doc.storage_url)
        if st is None:
            db.delete(doc)  # never uploaded
            continue
        if (st["size"] or 0) > MAX_FILE_BYTES:
            storage.delete(doc.storage_url)  # oversize → reject + remove bytes
            db.delete(doc)
            continue
        doc.size_bytes = st["size"]  # trust server-measured size
        if st.get("content_type"):
            doc.mime = st["content_type"]
        kept.append(doc)

    referral.status = ReferralStatus.READY
    referral.updated_at = datetime.utcnow()

    # Snapshot primitives BEFORE commit/session-close for the background task.
    recipients = _referral_recipients(clinic)
    payload = {
        "patient_name": referral.patient_name,
        "patient_phone": referral.patient_phone,
        "referred_by": referral.referred_by,
        "referrer_contact": referral.referrer_contact,
        "provider_label": _provider_label(db, clinic, referral.provider_id),
        "proposed_extraction_date": (
            referral.proposed_extraction_date.isoformat()
            if referral.proposed_extraction_date else None
        ),
        "tx_plan": referral.tx_plan,
        "submitted_at": referral.created_at.isoformat() if referral.created_at else "",
    }
    files = [{
        "object_key": d.storage_url,
        "original_name": d.original_name,
        "mime": d.mime,
        "size": d.size_bytes,
    } for d in kept]
    clinic_name = clinic.name

    db.commit()
    db.refresh(referral)

    from services.notifications import dispatch_referral_created
    try:
        background_tasks.add_task(
            dispatch_referral_created,
            recipients=recipients,
            clinic_name=clinic_name,
            referral=payload,
            files=files,
            storage=storage,
        )
    except Exception as e:  # never fail the request on notification scheduling
        logger.warning("Referral notification scheduling failed: %s", e)

    return referral


def _referral_recipients(clinic: Clinic) -> List[str]:
    from clients.email_client import resolve_clinic_recipients
    return resolve_clinic_recipients(clinic, kind="referral")

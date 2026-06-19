"""Referral business logic: create (mint upload tickets) + complete (verify + record + notify).

Flow (matches the spec):
  create_referral  → validate manifest, create Referral(status=NEW), return signed PUT tickets.
                     No referral_documents rows yet (abandoned referrals leave no orphan metadata).
  complete_referral→ the client reports which objects it uploaded; we treat that list as
                     authoritative but UNTRUSTED: each key must belong to this referral, the
                     object must actually exist in storage, be within the size limit, and carry
                     an allowed MIME. Surviving files become referral_documents; status → READY;
                     the clinic notification is dispatched. Idempotent (re-calls on a non-NEW
                     referral no-op and never re-send email).
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
    ReferralCompleteRequest,
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
    if not s or not s.strip():
        return None
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="invalid_extraction_date")


def _safe_ext(name: str) -> str:
    ext = Path(name or "").suffix
    return ext if (0 < len(ext) <= 8 and ext.replace(".", "").isalnum()) else ""


def create_referral(
    db: Session,
    *,
    clinic: Clinic,
    payload: ReferralCreateRequest,
    submit_ip: Optional[str],
    storage,
) -> Tuple[Referral, List[UploadTicket]]:
    """Validate, create the Referral (NEW), and return one signed PUT ticket per file.
    Does NOT create referral_documents or commit (caller commits)."""
    files = payload.files or []
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=422, detail=f"too_many_files:max_{MAX_FILES}")
    for f in files:
        if f.mime not in ALLOWED_MIME:
            raise HTTPException(status_code=422, detail=f"unsupported_type:{f.mime}")
        if (f.size or 0) > MAX_FILE_BYTES:
            raise HTTPException(status_code=422, detail="file_too_large")

    # Provider (if specified) must belong to this clinic and be active.
    if payload.provider_id is not None:
        ok = db.query(Provider).filter(
            Provider.id == payload.provider_id,
            Provider.clinic_id == clinic.id,
            Provider.is_active.is_(True),
        ).first()
        if ok is None:
            raise HTTPException(status_code=422, detail="invalid_provider")

    extraction_date = _parse_date(payload.proposed_extraction_date)

    referral = Referral(
        clinic_id=clinic.id,
        patient_name=payload.patient_name.strip(),
        patient_phone=payload.patient_phone.strip(),
        referred_by=payload.referred_by.strip(),
        referrer_contact=(payload.referrer_contact or "").strip() or None,
        proposed_extraction_date=extraction_date,
        tx_plan=(payload.tx_plan or "").strip() or None,
        provider_id=payload.provider_id,
        status=ReferralStatus.NEW,
        source="public-referral",
        submit_ip=submit_ip,
    )
    db.add(referral)
    db.flush()  # assign referral.id

    tickets: List[UploadTicket] = []
    for idx, f in enumerate(files):
        object_key = f"{clinic.id}/referrals/{referral.id}/{uuid.uuid4().hex}{_safe_ext(f.name)}"
        tickets.append(UploadTicket(
            file_index=idx,
            object_key=object_key,
            put_url=storage.signed_put_url(object_key, f.mime, MAX_FILE_BYTES),
            content_type=f.mime,
        ))
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
    payload: ReferralCompleteRequest,
    storage,
) -> Referral:
    """Record the uploaded files (client-reported but re-verified), mark READY, and
    schedule the clinic email. Idempotent: a non-NEW referral is returned untouched."""
    referral = db.query(Referral).filter(
        Referral.id == referral_id, Referral.clinic_id == clinic.id
    ).first()
    if referral is None:
        raise HTTPException(status_code=404, detail="referral_not_found")

    # Idempotency guard — never re-record or re-email an already-completed referral.
    if referral.status != ReferralStatus.NEW:
        return referral

    prefix = f"{clinic.id}/referrals/{referral.id}/"
    backend_name = "local" if storage.__class__.__name__ == "LocalBackend" else "gcs"
    seen_keys: set[str] = set()
    kept: List[ReferralDocument] = []

    for f in (payload.files or []):
        key = (f.object_key or "").strip()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        # Key must belong to THIS referral (defends against forged/cross-referral keys).
        if not key.startswith(prefix) or "/.." in key or key.endswith("/.."):
            continue
        mime = (f.mime or "").strip()
        if mime and mime not in ALLOWED_MIME:
            storage.delete(key)  # disallowed type → remove the bytes, skip
            continue
        st = storage.stat(key)
        if st is None:
            continue  # never actually uploaded
        if (st["size"] or 0) > MAX_FILE_BYTES:
            storage.delete(key)  # oversize → reject + remove
            continue
        # Prefer the storage-reported content type when it is an allowed type;
        # otherwise fall back to the (allowed) manifest mime.
        st_mime = (st.get("content_type") or "").strip()
        final_mime = st_mime if st_mime in ALLOWED_MIME else (mime or None)
        if final_mime is not None and final_mime not in ALLOWED_MIME:
            storage.delete(key)
            continue
        doc = ReferralDocument(
            clinic_id=clinic.id,
            referral_id=referral.id,
            kind=_kind_for_mime(final_mime or ""),
            storage_url=key,
            storage_backend=backend_name,
            mime=final_mime,
            size_bytes=st["size"],
            original_name=f.name,
        )
        db.add(doc)
        kept.append(doc)

    referral.status = ReferralStatus.READY
    referral.updated_at = datetime.utcnow()

    # Snapshot primitives BEFORE commit/session-close for the background task.
    recipients = _referral_recipients(clinic)
    payload_data = {
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
            referral=payload_data,
            files=files,
            storage=storage,
        )
    except Exception as e:  # never fail the request on notification scheduling
        logger.warning("Referral notification scheduling failed: %s", e)

    return referral


def _referral_recipients(clinic: Clinic) -> List[str]:
    from clients.email_client import resolve_clinic_recipients
    return resolve_clinic_recipients(clinic, kind="referral")

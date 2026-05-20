"""Communications v2 router: send, log, inbound webhooks."""

import os
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Patient
from database.ops.models import Communication
from api.main import get_clinic
from clients.sms_client import _send_sms_sync, SEND_BOOKING_SMS, send_whatsapp

router = APIRouter(prefix="/api/v2/communications", tags=["v2-communications"])


class SendIn(BaseModel):
    patient_id: str
    channel: str  # sms|email
    body: str
    related_appointment_id: Optional[str] = None
    related_invoice_id: Optional[str] = None


def _comm_out(c: Communication) -> dict:
    return {
        "id": c.id,
        "clinic_id": c.clinic_id,
        "patient_id": c.patient_id,
        "channel": c.channel,
        "direction": c.direction,
        "body": c.body,
        "status": c.status,
        "thread_key": c.thread_key,
        "read_at": c.read_at.isoformat() if c.read_at else None,
        "attachments": c.attachments or [],
        "related_appointment_id": c.related_appointment_id,
        "related_invoice_id": c.related_invoice_id,
        "created_at": c.created_at.isoformat(),
        "sent_at": c.sent_at.isoformat() if c.sent_at else None,
    }


def _send_patient_message(channel: str, patient: Patient, body: str) -> bool:
    """Dispatch message via existing helpers. Returns True on success."""
    if channel == "sms":
        if patient.phone:
            return _send_sms_sync(patient.phone, body)
        return False
    elif channel == "whatsapp":
        if patient.phone:
            result = send_whatsapp(to=patient.phone, body=body)
            return result.get("sid") is not None
        return False
    elif channel == "email":
        # Stub: log only (no SMTP for patient messages in v1)
        import logging
        logging.getLogger("dental-receptionist").info(
            "Patient email (stub): to=%s body=%s", patient.email, body[:80]
        )
        return True
    return False


@router.post("/send", status_code=201)
def send_communication(body: SendIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == body.patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    comm = Communication(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        channel=body.channel,
        direction="out",
        body=body.body,
        status="queued",
        thread_key=f"{body.patient_id}:{body.channel}",
        related_appointment_id=body.related_appointment_id,
        related_invoice_id=body.related_invoice_id,
    )
    db.add(comm)
    db.flush()

    ok = _send_patient_message(body.channel, patient, body.body)
    comm.status = "sent" if ok else "failed"
    if ok:
        comm.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(comm)
    return _comm_out(comm)


@router.get("")
def list_communications(
    patient_id: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(Communication).filter(Communication.clinic_id == clinic.id)
    if patient_id:
        q = q.filter(Communication.patient_id == patient_id)
    if channel:
        q = q.filter(Communication.channel == channel)
    return [_comm_out(c) for c in q.order_by(Communication.created_at.desc()).all()]


@router.patch("/threads/{thread_key}/read")
def mark_thread_read(thread_key: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = (
        db.query(Communication)
        .filter(
            Communication.clinic_id == clinic.id,
            Communication.thread_key == thread_key,
            Communication.read_at.is_(None),
        )
        .all()
    )
    for r in rows:
        r.read_at = now
    db.commit()
    return {"updated": len(rows)}


# ---------------------------------------------------------------------------
# Inbound webhooks
# ---------------------------------------------------------------------------

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def _verify_webhook(x_webhook_secret: Optional[str] = Header(None)):
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(401, "Invalid webhook secret")


@router.post("/inbound/sms", status_code=200, dependencies=[Depends(_verify_webhook)])
def inbound_sms(payload: dict, db: Session = Depends(get_db)):
    """Twilio inbound SMS webhook stub."""
    from_number = payload.get("From", "")
    body = payload.get("Body", "")

    # Try to find patient by phone
    patient = db.query(Patient).filter(Patient.phone == from_number).first()
    if patient:
        comm = Communication(
            clinic_id=patient.clinic_id,
            patient_id=patient.id,
            channel="inbound_sms",
            direction="in",
            body=body,
            status="received",
        )
        db.add(comm)
        db.commit()
    return {"status": "received"}


@router.post("/inbound/email", status_code=200, dependencies=[Depends(_verify_webhook)])
def inbound_email(payload: dict, db: Session = Depends(get_db)):
    """SMTP inbound email webhook stub."""
    from_email = payload.get("from", "")
    body = payload.get("body", payload.get("text", ""))

    patient = db.query(Patient).filter(Patient.email == from_email).first()
    if patient:
        comm = Communication(
            clinic_id=patient.clinic_id,
            patient_id=patient.id,
            channel="inbound_email",
            direction="in",
            body=body,
            status="received",
        )
        db.add(comm)
        db.commit()
    return {"status": "received"}

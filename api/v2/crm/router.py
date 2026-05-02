"""CRM v2 router: lead conversion, lead events, marketing campaigns."""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, Lead, LeadStatus, Patient, DEFAULT_CLINIC_ID
from database.ops.models import LeadEvent, MarketingCampaign
from api.main import get_clinic

router = APIRouter(prefix="/api/v2/crm", tags=["v2-crm"])


# ---------------------------------------------------------------------------
# Lead conversion
# ---------------------------------------------------------------------------

class ConvertIn(BaseModel):
    create_patient: bool = True


@router.post("/leads/{lead_id}/convert", status_code=200)
def convert_lead(lead_id: str, body: ConvertIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    # Idempotent: check if already converted
    existing_event = db.query(LeadEvent).filter(
        LeadEvent.lead_id == lead_id,
        LeadEvent.kind == "converted",
    ).first()

    if existing_event and existing_event.payload and existing_event.payload.get("patient_id"):
        existing_patient = db.query(Patient).filter(
            Patient.id == existing_event.payload["patient_id"]
        ).first()
        if existing_patient:
            return {
                "lead_id": lead_id,
                "patient_id": existing_patient.id,
                "created": False,
            }

    patient_id = None
    if body.create_patient:
        # Parse name
        parts = (lead.name or "").split(" ", 1)
        first = parts[0] if parts else None
        last = parts[1] if len(parts) > 1 else None

        patient = Patient(
            clinic_id=clinic.id,
            first_name=first,
            last_name=last,
            phone=lead.phone,
            email=lead.email,
        )
        db.add(patient)
        db.flush()
        patient_id = patient.id

    lead.status = LeadStatus.CONVERTED
    db.add(LeadEvent(
        lead_id=lead_id,
        kind="converted",
        payload={"patient_id": patient_id, "source": lead.source},
    ))
    db.commit()

    return {
        "lead_id": lead_id,
        "patient_id": patient_id,
        "created": True,
    }


# ---------------------------------------------------------------------------
# Lead events
# ---------------------------------------------------------------------------

class LeadEventIn(BaseModel):
    kind: str  # note|status_change|email_sent|sms_sent|converted
    payload: Optional[dict] = None


@router.post("/leads/{lead_id}/events", status_code=201)
def create_lead_event(lead_id: str, body: LeadEventIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    event = LeadEvent(lead_id=lead_id, kind=body.kind, payload=body.payload)
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "lead_id": event.lead_id, "kind": event.kind, "occurred_at": event.occurred_at.isoformat()}


@router.get("/leads/{lead_id}/events")
def list_lead_events(lead_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    events = db.query(LeadEvent).filter(LeadEvent.lead_id == lead_id).order_by(LeadEvent.occurred_at).all()
    return [
        {"id": e.id, "lead_id": e.lead_id, "kind": e.kind, "occurred_at": e.occurred_at.isoformat(), "payload": e.payload}
        for e in events
    ]


# ---------------------------------------------------------------------------
# Marketing campaigns
# ---------------------------------------------------------------------------

class CampaignIn(BaseModel):
    name: str
    audience_query: Optional[dict] = None
    schedule_at: Optional[str] = None
    channel: str
    body_template: str


def _campaign_out(c: MarketingCampaign) -> dict:
    return {
        "id": c.id,
        "clinic_id": c.clinic_id,
        "name": c.name,
        "channel": c.channel,
        "status": c.status,
        "schedule_at": c.schedule_at.isoformat() if c.schedule_at else None,
        "created_at": c.created_at.isoformat(),
    }


@router.post("/marketing-campaigns", status_code=201)
def create_campaign(body: CampaignIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    schedule_at = None
    if body.schedule_at:
        from api.v2.scheduling.router import _parse_dt
        schedule_at = _parse_dt(body.schedule_at)

    campaign = MarketingCampaign(
        clinic_id=clinic.id,
        name=body.name,
        audience_query=body.audience_query,
        schedule_at=schedule_at,
        channel=body.channel,
        body_template=body.body_template,
        status="draft",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _campaign_out(campaign)


@router.get("/marketing-campaigns")
def list_campaigns(clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    campaigns = db.query(MarketingCampaign).filter(MarketingCampaign.clinic_id == clinic.id).all()
    return [_campaign_out(c) for c in campaigns]


@router.post("/marketing-campaigns/{campaign_id}/send", status_code=200)
def send_campaign(campaign_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    campaign = db.query(MarketingCampaign).filter(
        MarketingCampaign.id == campaign_id, MarketingCampaign.clinic_id == clinic.id
    ).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status not in ("draft", "scheduled"):
        raise HTTPException(400, f"Cannot send campaign in status '{campaign.status}'")
    campaign.status = "sent"
    db.commit()
    return _campaign_out(campaign)

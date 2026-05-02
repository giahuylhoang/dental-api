"""Settings router: clinic config + integrations health."""
import os
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic
from api.main import get_clinic

router = APIRouter(prefix="/api/v2/settings", tags=["v2-settings"])


class ClinicConfigOut(BaseModel):
    display_name: Optional[str]
    timezone: Optional[str]
    working_hour_start: Optional[int]
    working_hour_end: Optional[int]
    address: Optional[str]
    contact_phone: Optional[str]
    booking_notification_email: Optional[str]


class ClinicConfigPatch(BaseModel):
    display_name: Optional[str] = None
    timezone: Optional[str] = None
    working_hour_start: Optional[int] = None
    working_hour_end: Optional[int] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    booking_notification_email: Optional[str] = None


def _clinic_to_config(clinic: Clinic) -> dict:
    return {
        "display_name": clinic.display_name or clinic.id,
        "timezone": clinic.timezone,
        "working_hour_start": clinic.working_hour_start,
        "working_hour_end": clinic.working_hour_end,
        "address": clinic.address,
        "contact_phone": clinic.contact_phone,
        "booking_notification_email": clinic.booking_notification_email,
    }


@router.get("/clinic", response_model=ClinicConfigOut)
def get_clinic_config(clinic: Clinic = Depends(get_clinic)):
    return _clinic_to_config(clinic)


@router.put("/clinic", response_model=ClinicConfigOut)
def update_clinic_config(
    body: ClinicConfigPatch,
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)
    db.commit()
    db.refresh(clinic)
    return _clinic_to_config(clinic)


@router.get("/integrations")
def get_integrations():
    return {
        "sms": {"enabled": bool(os.getenv("TWILIO_ACCOUNT_SID"))},
        "email": {"enabled": bool(os.getenv("SMTP_HOST"))},
        "whatsapp": {"enabled": bool(os.getenv("TWILIO_WHATSAPP_FROM"))},
    }

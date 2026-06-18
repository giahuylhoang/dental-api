from typing import Optional
from pydantic import BaseModel


class PublicHoldRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    new_patient: bool
    provider_id: Optional[int] = None
    service_id: Optional[int] = None
    service_name: str = "Consultation"
    start_time: str
    end_time: str
    insurance: Optional[str] = None
    insurance_other: Optional[str] = None
    message: Optional[str] = None
    # recaptcha_token is verified by the BFF (see spec §5); dental-api accepts but
    # does not re-verify it here. Kept so the forwarded body validates cleanly.
    recaptcha_token: Optional[str] = None


class PublicHoldResponse(BaseModel):
    appointment_id: str
    status: str
    provider_id: int
    start_time: str
    end_time: str

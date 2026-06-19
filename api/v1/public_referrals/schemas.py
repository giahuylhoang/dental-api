"""Schemas + limits for the public referral endpoints."""
import os
from typing import List, Optional

from pydantic import BaseModel

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/heic", "image/heif", "image/webp", "application/pdf",
}
MAX_FILES = int(os.getenv("REFERRAL_MAX_FILES", "10"))
MAX_FILE_BYTES = int(os.getenv("REFERRAL_MAX_FILE_MB", "15")) * 1024 * 1024


class FileManifestItem(BaseModel):
    name: str
    mime: str
    size: int


class ReferralCreateRequest(BaseModel):
    patient_name: str
    patient_phone: str
    referred_by: str
    referrer_contact: Optional[str] = None
    proposed_extraction_date: Optional[str] = None  # 'YYYY-MM-DD'
    tx_plan: Optional[str] = None
    provider_id: Optional[int] = None               # null = "Either"
    files: List[FileManifestItem] = []
    # Honeypot + reCAPTCHA are enforced at the BFF; accepted here so the
    # forwarded JSON validates cleanly. Not re-verified.
    recaptcha_token: Optional[str] = None
    company: Optional[str] = None                    # honeypot mirror


class UploadTicket(BaseModel):
    file_index: int
    object_key: str
    put_url: str
    content_type: str


class ReferralCreateResponse(BaseModel):
    referral_id: str
    status: str
    uploads: List[UploadTicket]


class CompletedFile(BaseModel):
    object_key: str
    name: Optional[str] = None     # original filename (display only)
    mime: Optional[str] = None     # claimed; re-checked against ALLOWED_MIME + storage
    size: Optional[int] = None     # claimed; ignored in favour of storage stat()


class ReferralCompleteRequest(BaseModel):
    files: List[CompletedFile] = []


class ReferralCompleteResponse(BaseModel):
    referral_id: str
    status: str
    documents: int

"""Token-based reschedule handoff.

GET /p/reschedule/{token}
  - 302 -> MARKET_MALL_WEBSITE_BASE_URL/reschedule?session=<signed_blob>
  - 404 unknown token
  - 410 expired / used token
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone

import nacl.signing
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Appointment
from database.ops.models import AppointmentReminder

router = APIRouter(prefix="/p", tags=["public"])


def _sign_session(payload: dict) -> str:
    """Ed25519-sign a JSON payload with the dental-api private key seed.

    Reads RESCHEDULE_SESSION_SIGNING_KEY (base64-seed) from env. The
    public key half is shared with market-mall-website's BFF out of band.
    """
    seed_b64 = os.environ["RESCHEDULE_SESSION_SIGNING_KEY"]
    sk = nacl.signing.SigningKey(base64.b64decode(seed_b64))
    body = json.dumps(payload, separators=(",", ":")).encode()
    signed = sk.sign(body)
    # Combine signature + body, URL-safe base64 so it fits in a query param.
    return base64.urlsafe_b64encode(signed.signature + b"||" + body).decode()


@router.get("/reschedule/{token}")
def get_reschedule(token: str, db: Session = Depends(get_db)):
    reminder = (
        db.query(AppointmentReminder)
        .filter_by(reschedule_token=token)
        .first()
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="token not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if reminder.reschedule_token_used_at is not None:
        raise HTTPException(status_code=410, detail="token already used")
    if (
        reminder.reschedule_token_expires_at
        and reminder.reschedule_token_expires_at <= now
    ):
        raise HTTPException(status_code=410, detail="token expired")

    # AppointmentReminder has no `appointment` relationship — query directly,
    # matching the pattern used by api/webhooks/telnyx.py.
    appt = (
        db.query(Appointment).filter_by(id=reminder.appointment_id).first()
    )
    if appt is None:
        # Reminder points to a vanished appointment — treat as gone.
        raise HTTPException(status_code=410, detail="appointment missing")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    session = _sign_session(
        {
            "appointment_id": appt.id,
            "patient_id": appt.patient_id,
            "clinic_id": appt.clinic_id,
            "iat": now_ts,
            "exp": now_ts + 1800,  # 30-min TTL
        }
    )
    base = os.environ.get("MARKET_MALL_WEBSITE_BASE_URL", "").rstrip("/")
    return RedirectResponse(
        url=f"{base}/reschedule?session={session}", status_code=302
    )

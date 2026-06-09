"""Token-based reschedule handoff.

GET /p/reschedule/{token}
  - 302 -> MARKET_MALL_WEBSITE_BASE_URL/reschedule?session=<signed_blob>
  - 404 unknown token
  - 410 expired / used token

POST /p/reschedule/{token}/commit
  - Auth: X-Internal-Secret (called by market-mall-website's BFF).
  - Body: {"hold_id": "<appointment_id of PENDING hold>"}
  - Atomically swaps: old appointment -> RESCHEDULED, hold-appointment -> SCHEDULED,
    reminder.reschedule_token_used_at flipped.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone

import nacl.signing
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import require_internal_secret
from database.connection import get_db
from database.models import Appointment, AppointmentStatus
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


class CommitRequest(BaseModel):
    hold_id: str


@router.post(
    "/reschedule/{token}/commit",
    dependencies=[Depends(require_internal_secret)],
)
def post_commit(
    token: str, body: CommitRequest, db: Session = Depends(get_db)
):
    """Commit a hold against a reschedule token.

    The holds-foundation system represents a hold as an `Appointment` row with
    `status=PENDING` and `hold_expiry_at` set; there is no separate Hold model.
    So `body.hold_id` is the PENDING-Appointment id created via POST /api/public/holds.

    On success:
      - old appointment        -> RESCHEDULED
      - hold-appointment       -> SCHEDULED (hold_expiry_at cleared)
      - reminder.reschedule_token_used_at -> now
    """
    reminder = (
        db.query(AppointmentReminder)
        .filter_by(reschedule_token=token)
        .first()
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="token not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if reminder.reschedule_token_used_at is not None or (
        reminder.reschedule_token_expires_at
        and reminder.reschedule_token_expires_at <= now
    ):
        raise HTTPException(status_code=410, detail="token expired or used")

    old_appt = (
        db.query(Appointment).filter_by(id=reminder.appointment_id).first()
    )
    if old_appt is None:
        raise HTTPException(status_code=410, detail="appointment missing")

    hold = db.query(Appointment).filter_by(id=body.hold_id).first()
    if (
        hold is None
        or hold.status != AppointmentStatus.PENDING
        or hold.patient_id != old_appt.patient_id
        or hold.clinic_id != old_appt.clinic_id
    ):
        raise HTTPException(status_code=409, detail="hold mismatch")
    if hold.hold_expiry_at and hold.hold_expiry_at <= now:
        raise HTTPException(status_code=409, detail="hold expired")

    # Atomically swap. Mirrors services.holds.confirm_hold (PENDING -> SCHEDULED,
    # hold_expiry cleared) but skips the staff-confirm SMS path — the patient
    # already picked their slot in the market-mall BFF.
    old_appt.status = AppointmentStatus.RESCHEDULED
    hold.status = AppointmentStatus.SCHEDULED
    hold.hold_expiry_at = None
    reminder.reschedule_token_used_at = now
    db.commit()

    return {
        "appointment_id": hold.id,
        "start_time": hold.start_time.isoformat(),
    }

"""POST /api/calls — receives call records from the v3 agent shutdown hook.

The agent shutdown writer migration is a separate follow-up spec; this endpoint
exists now so dental-api is ready to receive.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_authorized_clinic, get_db
from api.v1.calls.schemas import CallRecordIn
from database.models import CallLog, Clinic

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("", status_code=201)
def post_call(
    body: CallRecordIn,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_authorized_clinic),
):
    """Upsert a call log row by id.

    Note: the decorator returns 201 even on update. This is intentional —
    idempotent semantics from the caller's perspective (the row exists either
    way). Tests accept 200 OR 201 for the duplicate-id case.
    """
    row = db.query(CallLog).filter_by(id=body.id).first()
    if row is None:
        row = CallLog(
            id=body.id,
            clinic_id=clinic.id,
            caller_phone=body.caller_phone,
            patient_id=body.patient_id,
            started_at=body.started_at,
            ended_at=body.ended_at,
            duration_sec=body.duration_sec,
            outcome=body.outcome,
            transcript=body.transcript,
            audio_url=body.audio_url,
            call_metadata=body.metadata,
        )
        db.add(row)
    else:
        # Upsert — overwrite mutable fields
        for f in (
            "caller_phone",
            "patient_id",
            "ended_at",
            "duration_sec",
            "outcome",
            "transcript",
            "audio_url",
        ):
            setattr(row, f, getattr(body, f))
        row.call_metadata = body.metadata
    db.commit()
    return {"id": row.id, "status": "ok"}

"""Scheduling v2 router: operatories, appointments with recurrence, waitlist, recall, calendar."""

import json
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import (
    Appointment, AppointmentStatus, Patient, Provider, Service, Clinic,
    ProviderBusyBlock, DEFAULT_CLINIC_ID,
)
from database.ops.models import (
    Operatory, AppointmentResource, AppointmentRecurrence,
    AppointmentReminder, WaitlistEntry, RecallRule, Recall,
)
from api.dependencies import get_authorized_clinic
from services.tz_utils import to_clinic_local, to_storage_utc_clinic

router = APIRouter(prefix="/api/v2/scheduling", tags=["v2-scheduling"])

ACTIVE_STATUSES = (
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.PENDING_SYNC,
    AppointmentStatus.PENDING,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_dt(s: str) -> datetime:
    """Parse an ISO-ish datetime string.

    Offset-free input returns a naive datetime (interpreted downstream as
    clinic-local wall-clock via ``to_storage_utc_clinic``). Offset-aware input
    is returned **with its offset preserved** — never stripped — so the caller's
    conversion honors the caller's stated zone. ``datetime.fromisoformat`` parses
    offsets in 3.11+, so we delegate the aware branch to it."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    # Fallback: ISO 8601 (incl. offset / 'Z'). Preserves any tzinfo present.
    return datetime.fromisoformat(s)


def _check_provider_conflict(db: Session, clinic_id: str, provider_id: int,
                              start: datetime, end: datetime, exclude_id: str = None):
    q = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.provider_id == provider_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.start_time < end,
        Appointment.end_time > start,
    )
    if exclude_id:
        q = q.filter(Appointment.id != exclude_id)
    return q.first()


def _check_operatory_conflict(db: Session, operatory_id: str,
                               start: datetime, end: datetime, exclude_apt_id: str = None):
    q = db.query(AppointmentResource).join(
        Appointment, AppointmentResource.appointment_id == Appointment.id
    ).filter(
        AppointmentResource.operatory_id == operatory_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.start_time < end,
        Appointment.end_time > start,
    )
    if exclude_apt_id:
        q = q.filter(AppointmentResource.appointment_id != exclude_apt_id)
    return q.first()


# ---------------------------------------------------------------------------
# Operatories
# ---------------------------------------------------------------------------

class RescheduleRequest(BaseModel):
    start_time: datetime
    end_time: datetime


class OperatoryIn(BaseModel):
    name: str
    equipment_tags: Optional[list] = None
    is_active: bool = True


class OperatoryOut(BaseModel):
    id: str
    clinic_id: str
    name: str
    equipment_tags: Optional[list] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/operatories", response_model=List[OperatoryOut])
def list_operatories(clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    return db.query(Operatory).filter(Operatory.clinic_id == clinic.id).all()


@router.post("/operatories", response_model=OperatoryOut, status_code=201)
def create_operatory(body: OperatoryIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    op = Operatory(clinic_id=clinic.id, **body.model_dump())
    db.add(op)
    db.commit()
    db.refresh(op)
    return op


@router.put("/operatories/{op_id}", response_model=OperatoryOut)
def update_operatory(op_id: str, body: OperatoryIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    op = db.query(Operatory).filter(Operatory.id == op_id, Operatory.clinic_id == clinic.id).first()
    if not op:
        raise HTTPException(404, "Operatory not found")
    for k, v in body.model_dump().items():
        setattr(op, k, v)
    db.commit()
    db.refresh(op)
    return op


@router.delete("/operatories/{op_id}", status_code=204)
def delete_operatory(op_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    op = db.query(Operatory).filter(Operatory.id == op_id, Operatory.clinic_id == clinic.id).first()
    if not op:
        raise HTTPException(404, "Operatory not found")
    db.delete(op)
    db.commit()


# ---------------------------------------------------------------------------
# Provider busy blocks (recurring weekly windows when a provider is unavailable)
# ---------------------------------------------------------------------------

def _validate_busy_block_shape(
    weekdays: Optional[List[int]],
    specific_date: Optional[date],
    recurrence_until: Optional[date],
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int,
) -> None:
    """Shared validation for create and update. Raises ValueError on bad input."""
    if (start_hour, start_minute) >= (end_hour, end_minute):
        raise ValueError("start time must be before end time")
    has_wd = bool(weekdays)
    has_date = specific_date is not None
    if has_wd == has_date:
        raise ValueError("exactly one of weekdays or specific_date must be provided")
    if has_wd:
        if any(d < 0 or d > 6 for d in weekdays):
            raise ValueError("weekdays must be 0..6")
        if len(set(weekdays)) != len(weekdays):
            raise ValueError("weekdays must be unique")
    if has_date and recurrence_until is not None:
        raise ValueError("recurrence_until only applies to weekday rules")
    if recurrence_until is not None and recurrence_until < date.today():
        raise ValueError("recurrence_until must be today or later")


class BusyBlockIn(BaseModel):
    provider_id: int
    weekdays: Optional[List[int]] = None
    specific_date: Optional[date] = None
    recurrence_until: Optional[date] = None
    start_hour: int = Field(ge=0, le=23)
    start_minute: int = Field(ge=0, le=59, default=0)
    end_hour: int = Field(ge=0, le=23)
    end_minute: int = Field(ge=0, le=59, default=0)
    label: Optional[str] = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _validate(self):
        _validate_busy_block_shape(
            self.weekdays, self.specific_date, self.recurrence_until,
            self.start_hour, self.start_minute, self.end_hour, self.end_minute,
        )
        return self


class BusyBlockUpdate(BaseModel):
    weekdays: Optional[List[int]] = None
    specific_date: Optional[date] = None
    recurrence_until: Optional[date] = None
    start_hour: Optional[int] = Field(default=None, ge=0, le=23)
    start_minute: Optional[int] = Field(default=None, ge=0, le=59)
    end_hour: Optional[int] = Field(default=None, ge=0, le=23)
    end_minute: Optional[int] = Field(default=None, ge=0, le=59)
    label: Optional[str] = Field(default=None, max_length=64)


class BusyBlockOut(BaseModel):
    id: int
    provider_id: int
    weekdays: Optional[List[int]] = None
    specific_date: Optional[date] = None
    recurrence_until: Optional[date] = None
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    label: Optional[str] = None

    class Config:
        from_attributes = True


def _serialize_block(block: ProviderBusyBlock) -> BusyBlockOut:
    """Build a BusyBlockOut from the ORM row, decoding the JSON-encoded weekdays."""
    weekdays_list: Optional[List[int]] = None
    raw = block.weekdays
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                weekdays_list = [int(x) for x in parsed]
        except (json.JSONDecodeError, ValueError, TypeError):
            weekdays_list = None
    # Backward-compat: rows without `weekdays` but with legacy `weekday` get
    # surfaced as a single-element list.
    if weekdays_list is None and block.specific_date is None and block.weekday is not None:
        weekdays_list = [int(block.weekday)]
    return BusyBlockOut(
        id=block.id,
        provider_id=block.provider_id,
        weekdays=weekdays_list,
        specific_date=block.specific_date,
        recurrence_until=block.recurrence_until,
        start_hour=block.start_hour,
        start_minute=block.start_minute,
        end_hour=block.end_hour,
        end_minute=block.end_minute,
        label=block.label,
    )


@router.get("/busy-blocks", response_model=List[BusyBlockOut])
def list_busy_blocks(
    provider_id: Optional[int] = Query(default=None),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(ProviderBusyBlock).filter(ProviderBusyBlock.clinic_id == clinic.id)
    if provider_id is not None:
        q = q.filter(ProviderBusyBlock.provider_id == provider_id)
    rows = q.order_by(
        ProviderBusyBlock.provider_id,
        ProviderBusyBlock.specific_date,
        ProviderBusyBlock.start_hour,
        ProviderBusyBlock.start_minute,
    ).all()
    return [_serialize_block(r) for r in rows]


@router.post("/busy-blocks", response_model=BusyBlockOut, status_code=201)
def create_busy_block(
    body: BusyBlockIn,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(
        Provider.id == body.provider_id, Provider.clinic_id == clinic.id
    ).first()
    if provider is None:
        raise HTTPException(404, "Provider not found")
    block = ProviderBusyBlock(
        clinic_id=clinic.id,
        provider_id=body.provider_id,
        weekdays=json.dumps(sorted(body.weekdays)) if body.weekdays else None,
        specific_date=body.specific_date,
        recurrence_until=body.recurrence_until,
        start_hour=body.start_hour,
        start_minute=body.start_minute,
        end_hour=body.end_hour,
        end_minute=body.end_minute,
        label=body.label,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return _serialize_block(block)


@router.put("/busy-blocks/{block_id}", response_model=BusyBlockOut)
def update_busy_block(
    block_id: int,
    body: BusyBlockUpdate,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    block = db.query(ProviderBusyBlock).filter(
        ProviderBusyBlock.id == block_id, ProviderBusyBlock.clinic_id == clinic.id
    ).first()
    if block is None:
        raise HTTPException(404, "Busy block not found")
    patch = body.model_dump(exclude_unset=True)

    # Compute the post-patch field values for re-validation. Switching modes
    # via this PUT (e.g. supplying `specific_date` on a weekdays rule) clears
    # the other mode's fields — mirror that in the validation snapshot too.
    current_weekdays = json.loads(block.weekdays) if block.weekdays else None
    if "weekdays" in patch:
        new_weekdays = patch["weekdays"]
    elif "specific_date" in patch and patch["specific_date"] is not None:
        new_weekdays = None
    else:
        new_weekdays = current_weekdays

    if "specific_date" in patch:
        new_specific_date = patch["specific_date"]
    elif "weekdays" in patch and patch["weekdays"]:
        new_specific_date = None
    else:
        new_specific_date = block.specific_date

    if "recurrence_until" in patch:
        new_recurrence_until = patch["recurrence_until"]
    elif "specific_date" in patch and patch["specific_date"] is not None:
        new_recurrence_until = None
    else:
        new_recurrence_until = block.recurrence_until
    new_sh = patch.get("start_hour", block.start_hour)
    new_sm = patch.get("start_minute", block.start_minute)
    new_eh = patch.get("end_hour", block.end_hour)
    new_em = patch.get("end_minute", block.end_minute)
    try:
        _validate_busy_block_shape(
            new_weekdays, new_specific_date, new_recurrence_until,
            new_sh, new_sm, new_eh, new_em,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))

    if "weekdays" in patch:
        block.weekdays = json.dumps(sorted(patch["weekdays"])) if patch["weekdays"] else None
        # When switching to weekday mode, clear specific_date.
        if patch["weekdays"]:
            block.specific_date = None
            # Drop the legacy column so it doesn't get reused on read.
            block.weekday = None
    if "specific_date" in patch:
        block.specific_date = patch["specific_date"]
        # When switching to specific-date mode, clear recurrence fields.
        if patch["specific_date"] is not None:
            block.weekdays = None
            block.weekday = None
            block.recurrence_until = None
    if "recurrence_until" in patch:
        block.recurrence_until = patch["recurrence_until"]
    for k in ("start_hour", "start_minute", "end_hour", "end_minute", "label"):
        if k in patch:
            setattr(block, k, patch[k])
    db.commit()
    db.refresh(block)
    return _serialize_block(block)


@router.delete("/busy-blocks/{block_id}", status_code=204)
def delete_busy_block(
    block_id: int,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    block = db.query(ProviderBusyBlock).filter(
        ProviderBusyBlock.id == block_id, ProviderBusyBlock.clinic_id == clinic.id
    ).first()
    if block is None:
        raise HTTPException(404, "Busy block not found")
    db.delete(block)
    db.commit()


# ---------------------------------------------------------------------------
# Appointments (v2 — with operatory + recurrence)
# ---------------------------------------------------------------------------

class V2AppointmentIn(BaseModel):
    start_time: str
    end_time: str
    patient_id: str
    provider_id: int
    service_id: Optional[int] = None
    patient_name: str
    service_name: str
    reason: str = ""
    operatory_id: Optional[str] = None
    recurrence_rule: Optional[str] = None  # RRULE string


class V2AppointmentOut(BaseModel):
    appointment_id: str
    status: str
    recurrence_id: Optional[str] = None
    generated_count: int = 1


@router.post("/appointments", response_model=V2AppointmentOut, status_code=201)
def create_v2_appointment(body: V2AppointmentIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    # Parse on the clinic-local wall clock (naive) or as offset-aware if the
    # caller supplied an offset. Then convert to storage naive UTC at the write
    # boundary — the same contract the v1 router and holds use. Naive input is
    # treated as clinic-local; aware input is honored from its own zone.
    start_local = _parse_dt(body.start_time)
    end_local = _parse_dt(body.end_time)
    start = to_storage_utc_clinic(start_local, clinic)
    end = to_storage_utc_clinic(end_local, clinic)

    # Validate patient
    patient = db.query(Patient).filter(Patient.id == body.patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    # Validate provider
    provider = db.query(Provider).filter(Provider.id == body.provider_id, Provider.clinic_id == clinic.id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")

    # Provider conflict (compare converted UTC against stored naive-UTC rows)
    if _check_provider_conflict(db, clinic.id, body.provider_id, start, end):
        raise HTTPException(409, "Provider already has an appointment during this time slot")

    # Operatory conflict
    if body.operatory_id:
        op = db.query(Operatory).filter(Operatory.id == body.operatory_id, Operatory.clinic_id == clinic.id).first()
        if not op:
            raise HTTPException(404, "Operatory not found")
        if _check_operatory_conflict(db, body.operatory_id, start, end):
            raise HTTPException(409, "Operatory already booked during this time slot")

    # Create parent appointment (store naive UTC)
    apt = Appointment(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        provider_id=body.provider_id,
        service_id=body.service_id,
        start_time=start,
        end_time=end,
        reason_note=body.reason,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(apt)
    db.flush()

    if body.operatory_id:
        db.add(AppointmentResource(appointment_id=apt.id, operatory_id=body.operatory_id))

    recurrence_id = None
    generated_count = 1

    if body.recurrence_rule:
        from dateutil.rrule import rrulestr
        # Generate occurrences on the clinic-local wall clock so "9am Mondays"
        # stays 9am across DST, then convert EACH occurrence to storage UTC.
        # Canonical clinic-local wall clock of the anchor, regardless of the
        # caller's input zone. Generating from this keeps parent + children on
        # the same clinic-local time across DST and across cross-zone aware input.
        start_wall = to_clinic_local(start, clinic).replace(tzinfo=None)
        end_wall = to_clinic_local(end, clinic).replace(tzinfo=None)
        duration = end_wall - start_wall            # wall-clock delta
        try:
            rule = rrulestr(body.recurrence_rule, dtstart=start_wall, ignoretz=True)
        except Exception as e:
            raise HTTPException(400, f"Invalid RRULE: {e}")

        occurrences = list(rule)
        # Skip first (already created as parent)
        for occ in occurrences[1:]:
            occ_end = occ + duration
            occ_utc = to_storage_utc_clinic(occ, clinic)
            occ_end_utc = to_storage_utc_clinic(occ_end, clinic)
            if _check_provider_conflict(db, clinic.id, body.provider_id, occ_utc, occ_end_utc):
                db.rollback()
                raise HTTPException(409, f"Provider conflict on recurrence at {occ.isoformat()}")
            if body.operatory_id and _check_operatory_conflict(db, body.operatory_id, occ_utc, occ_end_utc):
                db.rollback()
                raise HTTPException(409, f"Operatory conflict on recurrence at {occ.isoformat()}")
            child = Appointment(
                clinic_id=clinic.id,
                patient_id=body.patient_id,
                provider_id=body.provider_id,
                service_id=body.service_id,
                start_time=occ_utc,
                end_time=occ_end_utc,
                reason_note=body.reason,
                status=AppointmentStatus.SCHEDULED,
            )
            db.add(child)
            db.flush()
            if body.operatory_id:
                db.add(AppointmentResource(appointment_id=child.id, operatory_id=body.operatory_id))
            generated_count += 1

        last_occ = occurrences[-1] if occurrences else start_wall
        rec = AppointmentRecurrence(
            clinic_id=clinic.id,
            parent_appointment_id=apt.id,
            rule=body.recurrence_rule,
            generated_through_date=last_occ,
        )
        db.add(rec)
        db.flush()
        recurrence_id = rec.id

    db.commit()
    return V2AppointmentOut(
        appointment_id=apt.id,
        status=apt.status.value,
        recurrence_id=recurrence_id,
        generated_count=generated_count,
    )


@router.post("/appointments/{apt_id}/cancel", status_code=200)
def cancel_v2_appointment(
    apt_id: str,
    cascade: bool = Query(False),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    apt = db.query(Appointment).filter(Appointment.id == apt_id, Appointment.clinic_id == clinic.id).first()
    if not apt:
        raise HTTPException(404, "Appointment not found")
    apt.status = AppointmentStatus.CANCELLED
    cancelled = [apt_id]

    if cascade:
        rec = db.query(AppointmentRecurrence).filter(
            AppointmentRecurrence.parent_appointment_id == apt_id
        ).first()
        if rec:
            # Cancel all appointments in the recurrence series (those with same parent)
            # We track by finding appointments linked via the recurrence
            # Simple approach: cancel all future appointments with same provider/patient/service
            siblings = db.query(Appointment).filter(
                Appointment.clinic_id == clinic.id,
                Appointment.patient_id == apt.patient_id,
                Appointment.provider_id == apt.provider_id,
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.start_time > apt.start_time,
            ).all()
            for s in siblings:
                s.status = AppointmentStatus.CANCELLED
                cancelled.append(s.id)

    db.commit()
    return {"cancelled": cancelled}


@router.post("/appointments/{apt_id}/reschedule", status_code=200)
def reschedule_v2_appointment(
    apt_id: str,
    body: RescheduleRequest,
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    apt = db.query(Appointment).filter(Appointment.id == apt_id, Appointment.clinic_id == clinic.id).first()
    if not apt:
        raise HTTPException(404, "Appointment not found")

    # body.start_time/end_time arrive already parsed by Pydantic (naive or
    # aware). Convert to storage naive UTC before conflict checks + insert.
    new_start = to_storage_utc_clinic(body.start_time, clinic)
    new_end = to_storage_utc_clinic(body.end_time, clinic)

    if _check_provider_conflict(db, clinic.id, apt.provider_id, new_start, new_end, exclude_id=apt_id):
        raise HTTPException(409, "Provider conflict at new time")

    # Check operatory if assigned
    res = db.query(AppointmentResource).filter(AppointmentResource.appointment_id == apt_id).first()
    if res and _check_operatory_conflict(db, res.operatory_id, new_start, new_end, exclude_apt_id=apt_id):
        raise HTTPException(409, "Operatory conflict at new time")

    apt.status = AppointmentStatus.RESCHEDULED
    new_apt = Appointment(
        clinic_id=clinic.id,
        patient_id=apt.patient_id,
        provider_id=apt.provider_id,
        service_id=apt.service_id,
        start_time=new_start,
        end_time=new_end,
        reason_note=apt.reason_note,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(new_apt)
    db.flush()
    if res:
        db.add(AppointmentResource(appointment_id=new_apt.id, operatory_id=res.operatory_id))
    db.commit()
    return {"appointment_id": new_apt.id, "status": new_apt.status.value}


# ---------------------------------------------------------------------------
# Calendar view
# ---------------------------------------------------------------------------

@router.get("/calendar")
def get_calendar(
    start: str = Query(...),
    end: str = Query(...),
    provider_id: Optional[int] = Query(None),
    operatory_id: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    # Request bounds arrive as clinic-local wall-clock; convert to naive UTC
    # before comparing against the UTC-stored start_time so a late-evening
    # local appt (stored on the next UTC day) is not dropped from a local day
    # window.
    start_dt = to_storage_utc_clinic(_parse_dt(start), clinic)
    end_dt = to_storage_utc_clinic(_parse_dt(end), clinic)

    q = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt,
    )
    if provider_id:
        q = q.filter(Appointment.provider_id == provider_id)

    apts = q.all()

    if operatory_id:
        apt_ids_with_op = {
            r.appointment_id for r in
            db.query(AppointmentResource).filter(AppointmentResource.operatory_id == operatory_id).all()
        }
        apts = [a for a in apts if a.id in apt_ids_with_op]

    return [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "provider_id": a.provider_id,
            "start_time": to_clinic_local(a.start_time, clinic).isoformat(),
            "end_time": to_clinic_local(a.end_time, clinic).isoformat(),
            "status": a.status.value,
        }
        for a in apts
    ]


# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------

class WaitlistIn(BaseModel):
    patient_id: str
    requested_window_start: str
    requested_window_end: str
    provider_pref: Optional[int] = None
    service_id: Optional[int] = None
    priority: int = 0


class WaitlistOut(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    requested_window_start: datetime
    requested_window_end: datetime
    provider_pref: Optional[int] = None
    service_id: Optional[int] = None
    priority: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/waitlist", response_model=WaitlistOut, status_code=201)
def add_to_waitlist(body: WaitlistIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    entry = WaitlistEntry(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        requested_window_start=to_storage_utc_clinic(_parse_dt(body.requested_window_start), clinic),
        requested_window_end=to_storage_utc_clinic(_parse_dt(body.requested_window_end), clinic),
        provider_pref=body.provider_pref,
        service_id=body.service_id,
        priority=body.priority,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/waitlist", response_model=List[WaitlistOut])
def list_waitlist(clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    return db.query(WaitlistEntry).filter(
        WaitlistEntry.clinic_id == clinic.id,
        WaitlistEntry.status == "open",
    ).order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()


@router.delete("/waitlist/{entry_id}", status_code=204)
def delete_waitlist_entry(entry_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id, WaitlistEntry.clinic_id == clinic.id).first()
    if not entry:
        raise HTTPException(404, "Waitlist entry not found")
    entry.status = "cancelled"
    db.commit()


@router.post("/waitlist/{entry_id}/fill", status_code=200)
def fill_waitlist_entry(
    entry_id: str,
    slot_start: str = Query(...),
    slot_end: str = Query(...),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    """Fill the highest-priority open waitlist entry whose window overlaps the slot."""
    slot_s = to_storage_utc_clinic(_parse_dt(slot_start), clinic)
    slot_e = to_storage_utc_clinic(_parse_dt(slot_end), clinic)

    # Find best match: window overlaps slot, highest priority, then FIFO
    entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.clinic_id == clinic.id,
        WaitlistEntry.status == "open",
        WaitlistEntry.requested_window_start < slot_e,
        WaitlistEntry.requested_window_end > slot_s,
    ).order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()

    if not entries:
        raise HTTPException(404, "No matching waitlist entry")

    entry = entries[0]
    entry.status = "filled"
    db.commit()
    return {"filled_entry_id": entry.id, "patient_id": entry.patient_id}


# ---------------------------------------------------------------------------
# Recall Rules
# ---------------------------------------------------------------------------

class RecallRuleIn(BaseModel):
    name: str
    trigger_event: str
    offset_days: int
    channel: str = "sms"


class RecallRuleOut(BaseModel):
    id: str
    clinic_id: str
    name: str
    trigger_event: str
    offset_days: int
    channel: str

    class Config:
        from_attributes = True


@router.post("/recall-rules", response_model=RecallRuleOut, status_code=201)
def create_recall_rule(body: RecallRuleIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    rule = RecallRule(clinic_id=clinic.id, **body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/recall-rules", response_model=List[RecallRuleOut])
def list_recall_rules(clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    return db.query(RecallRule).filter(RecallRule.clinic_id == clinic.id).all()


@router.put("/recall-rules/{rule_id}", response_model=RecallRuleOut)
def update_recall_rule(rule_id: str, body: RecallRuleIn, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    rule = db.query(RecallRule).filter(RecallRule.id == rule_id, RecallRule.clinic_id == clinic.id).first()
    if not rule:
        raise HTTPException(404, "Recall rule not found")
    for k, v in body.model_dump().items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/recall-rules/{rule_id}", status_code=204)
def delete_recall_rule(rule_id: str, clinic: Clinic = Depends(get_authorized_clinic), db: Session = Depends(get_db)):
    rule = db.query(RecallRule).filter(RecallRule.id == rule_id, RecallRule.clinic_id == clinic.id).first()
    if not rule:
        raise HTTPException(404, "Recall rule not found")
    db.delete(rule)
    db.commit()


@router.get("/recalls")
def list_recalls(
    status: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_authorized_clinic),
    db: Session = Depends(get_db),
):
    q = db.query(Recall).filter(Recall.clinic_id == clinic.id)
    if status:
        q = q.filter(Recall.status == status)
    recalls = q.all()
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "rule_id": r.rule_id,
            "due_at": r.due_at.isoformat(),
            "status": r.status,
        }
        for r in recalls
    ]

"""Scheduling v2 router: operatories, appointments with recurrence, waitlist, recall, calendar."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import (
    Appointment, AppointmentStatus, Patient, Provider, Service, Clinic, DEFAULT_CLINIC_ID
)
from database.ops.models import (
    Operatory, AppointmentResource, AppointmentRecurrence,
    AppointmentReminder, WaitlistEntry, RecallRule, Recall,
)
from api.main import get_clinic

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
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    # Try ISO with timezone offset — strip tz for naive comparison
    import re
    s_clean = re.sub(r'[+-]\d{2}:\d{2}$', '', s).rstrip('Z')
    return datetime.fromisoformat(s_clean)


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
def list_operatories(clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return db.query(Operatory).filter(Operatory.clinic_id == clinic.id).all()


@router.post("/operatories", response_model=OperatoryOut, status_code=201)
def create_operatory(body: OperatoryIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    op = Operatory(clinic_id=clinic.id, **body.model_dump())
    db.add(op)
    db.commit()
    db.refresh(op)
    return op


@router.put("/operatories/{op_id}", response_model=OperatoryOut)
def update_operatory(op_id: str, body: OperatoryIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    op = db.query(Operatory).filter(Operatory.id == op_id, Operatory.clinic_id == clinic.id).first()
    if not op:
        raise HTTPException(404, "Operatory not found")
    for k, v in body.model_dump().items():
        setattr(op, k, v)
    db.commit()
    db.refresh(op)
    return op


@router.delete("/operatories/{op_id}", status_code=204)
def delete_operatory(op_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    op = db.query(Operatory).filter(Operatory.id == op_id, Operatory.clinic_id == clinic.id).first()
    if not op:
        raise HTTPException(404, "Operatory not found")
    db.delete(op)
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
def create_v2_appointment(body: V2AppointmentIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    start = _parse_dt(body.start_time)
    end = _parse_dt(body.end_time)

    # Validate patient
    patient = db.query(Patient).filter(Patient.id == body.patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    # Validate provider
    provider = db.query(Provider).filter(Provider.id == body.provider_id, Provider.clinic_id == clinic.id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")

    # Provider conflict
    if _check_provider_conflict(db, clinic.id, body.provider_id, start, end):
        raise HTTPException(409, "Provider already has an appointment during this time slot")

    # Operatory conflict
    if body.operatory_id:
        op = db.query(Operatory).filter(Operatory.id == body.operatory_id, Operatory.clinic_id == clinic.id).first()
        if not op:
            raise HTTPException(404, "Operatory not found")
        if _check_operatory_conflict(db, body.operatory_id, start, end):
            raise HTTPException(409, "Operatory already booked during this time slot")

    # Create parent appointment
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
        duration = end - start
        try:
            rule = rrulestr(body.recurrence_rule, dtstart=start, ignoretz=True)
        except Exception as e:
            raise HTTPException(400, f"Invalid RRULE: {e}")

        occurrences = list(rule)
        # Skip first (already created as parent)
        for occ in occurrences[1:]:
            occ_end = occ + duration
            if _check_provider_conflict(db, clinic.id, body.provider_id, occ, occ_end):
                db.rollback()
                raise HTTPException(409, f"Provider conflict on recurrence at {occ.isoformat()}")
            if body.operatory_id and _check_operatory_conflict(db, body.operatory_id, occ, occ_end):
                db.rollback()
                raise HTTPException(409, f"Operatory conflict on recurrence at {occ.isoformat()}")
            child = Appointment(
                clinic_id=clinic.id,
                patient_id=body.patient_id,
                provider_id=body.provider_id,
                service_id=body.service_id,
                start_time=occ,
                end_time=occ_end,
                reason_note=body.reason,
                status=AppointmentStatus.SCHEDULED,
            )
            db.add(child)
            db.flush()
            if body.operatory_id:
                db.add(AppointmentResource(appointment_id=child.id, operatory_id=body.operatory_id))
            generated_count += 1

        last_occ = occurrences[-1] if occurrences else start
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
    clinic: Clinic = Depends(get_clinic),
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
    body: dict,
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    apt = db.query(Appointment).filter(Appointment.id == apt_id, Appointment.clinic_id == clinic.id).first()
    if not apt:
        raise HTTPException(404, "Appointment not found")

    new_start = _parse_dt(body["start_time"])
    new_end = _parse_dt(body["end_time"])

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
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)

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
            "start_time": a.start_time.isoformat(),
            "end_time": a.end_time.isoformat(),
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
def add_to_waitlist(body: WaitlistIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    entry = WaitlistEntry(
        clinic_id=clinic.id,
        patient_id=body.patient_id,
        requested_window_start=_parse_dt(body.requested_window_start),
        requested_window_end=_parse_dt(body.requested_window_end),
        provider_pref=body.provider_pref,
        service_id=body.service_id,
        priority=body.priority,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/waitlist", response_model=List[WaitlistOut])
def list_waitlist(clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return db.query(WaitlistEntry).filter(
        WaitlistEntry.clinic_id == clinic.id,
        WaitlistEntry.status == "open",
    ).order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()


@router.delete("/waitlist/{entry_id}", status_code=204)
def delete_waitlist_entry(entry_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
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
    clinic: Clinic = Depends(get_clinic),
    db: Session = Depends(get_db),
):
    """Fill the highest-priority open waitlist entry whose window overlaps the slot."""
    slot_s = _parse_dt(slot_start)
    slot_e = _parse_dt(slot_end)

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
def create_recall_rule(body: RecallRuleIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    rule = RecallRule(clinic_id=clinic.id, **body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/recall-rules", response_model=List[RecallRuleOut])
def list_recall_rules(clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    return db.query(RecallRule).filter(RecallRule.clinic_id == clinic.id).all()


@router.put("/recall-rules/{rule_id}", response_model=RecallRuleOut)
def update_recall_rule(rule_id: str, body: RecallRuleIn, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    rule = db.query(RecallRule).filter(RecallRule.id == rule_id, RecallRule.clinic_id == clinic.id).first()
    if not rule:
        raise HTTPException(404, "Recall rule not found")
    for k, v in body.model_dump().items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/recall-rules/{rule_id}", status_code=204)
def delete_recall_rule(rule_id: str, clinic: Clinic = Depends(get_clinic), db: Session = Depends(get_db)):
    rule = db.query(RecallRule).filter(RecallRule.id == rule_id, RecallRule.clinic_id == clinic.id).first()
    if not rule:
        raise HTTPException(404, "Recall rule not found")
    db.delete(rule)
    db.commit()


@router.get("/recalls")
def list_recalls(
    status: Optional[str] = Query(None),
    clinic: Clinic = Depends(get_clinic),
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

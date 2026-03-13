"""
FastAPI service for calendar and database operations.

Provides REST API endpoints for:
- Calendar operations (slots, events, sync)
- Database CRUD operations (patients, appointments, doctors, services)
"""

import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db, init_db
from database.models import Patient, Appointment, Doctor, Service, AppointmentStatus, Lead, LeadStatus, Clinic, DEFAULT_CLINIC_ID
from tools.slot_utils import get_available_slots
from clients.sms_client import (
    send_booking_sms_delayed,
    send_cancellation_sms_delayed,
    send_reschedule_sms_delayed,
)
import pytz
import logging

logger = logging.getLogger("dental-receptionist")

EDMONTON_TZ = pytz.timezone('America/Edmonton')


# Multi-tenant: resolve clinic from X-Clinic-Id header (default: "default")
def get_clinic_id(request: Request) -> str:
    clinic_id = request.headers.get("X-Clinic-Id", DEFAULT_CLINIC_ID)
    return clinic_id.strip() or DEFAULT_CLINIC_ID


def get_clinic(db: Session = Depends(get_db), clinic_id: str = Depends(get_clinic_id)):
    """Resolve Clinic by X-Clinic-Id. Raises 404 if not found."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
    return clinic


# Pydantic models for request/response
class AppointmentCreateRequest(BaseModel):
    """Request model for creating appointment."""
    start_time: str = Field(..., description="ISO datetime string")
    end_time: str = Field(..., description="ISO datetime string")
    patient_id: str
    doctor_id: int
    service_id: Optional[int] = None
    patient_name: str
    service_name: str
    reason: str


class AppointmentResponse(BaseModel):
    """Response model for appointment."""
    appointment_id: str
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None
    status: str


class PatientCreateRequest(BaseModel):
    """Request model for creating patient."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    is_minor: Optional[bool] = False
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    consent_approved: Optional[bool] = False


class PatientResponse(BaseModel):
    """Response model for patient."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


class PatientVerifyRequest(BaseModel):
    """Request model for patient verification."""
    phone: str = Field(..., description="Phone number to verify")
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")


class PatientVerifyResponse(BaseModel):
    """Response model for patient verification."""
    patient_id: str
    verified: bool = True


class LeadCreateRequest(BaseModel):
    """Request model for creating lead."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    """Request model for updating lead."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Response model for lead."""
    id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeadStatusUpdateRequest(BaseModel):
    """Request model for updating lead status."""
    status: str = Field(..., description="New status value (e.g., NEW, CONTACTED, QUALIFIED, CONVERTED, LOST)")


class AppointmentStatusUpdateRequest(BaseModel):
    """Request model for updating appointment status."""
    status: str = Field(..., description="New status value (e.g., CONFIRMED, REMINDER_SENT, CANCELLED)")


class AppointmentDetailResponse(BaseModel):
    """Detailed appointment response."""
    id: str
    patient_id: str
    doctor_id: int
    service_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    reason_note: Optional[str] = None
    status: str
    calendar_event_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    try:
        init_db()
        logger.info("Database tables ready")
    except Exception as e:
        logger.warning("Database init failed: %s", e)
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="Dental Clinic Calendar API",
    description="API for calendar and database operations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: allow frontend (Vite often on 5173 or 5174 when 5173 is in use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:5174", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Calendar Endpoints
# ============================================================================

@app.get("/api/calendar/slots")
async def get_calendar_slots(
    start_datetime: str = Query(..., description="ISO datetime string"),
    end_datetime: str = Query(..., description="ISO datetime string"),
    doctor_id: Optional[int] = Query(None, description="Doctor ID for filtering"),
    doctor_name: Optional[str] = Query(None, description="Doctor name for filtering"),
    slot_minutes: int = Query(30, description="Slot duration in minutes"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Get available appointment slots for a datetime range (computed from database).
    Per-clinic working hours and timezone from X-Clinic-Id.
    """
    try:
        slots = get_available_slots(
            db=db,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            slot_minutes=slot_minutes,
            clinic_id=clinic.id,
            timezone_str=clinic.timezone,
            hour_start=clinic.working_hour_start,
            hour_end=clinic.working_hour_end,
        )
        return {"slots": slots}
    except Exception as e:
        logger.error(f"Error in get_calendar_slots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calendar/events")
async def create_calendar_event(
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create appointment in database (DB is source of truth)."""
    # 0. Validate datetime formats BEFORE creating appointment
    try:
        start_time_dt = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid start_time format: {str(e)}. Expected ISO datetime format."
        )
    
    try:
        end_time_dt = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid end_time format: {str(e)}. Expected ISO datetime format."
        )
    
    # Validate end_time is after start_time
    if end_time_dt <= start_time_dt:
        raise HTTPException(
            status_code=400,
            detail="end_time must be after start_time"
        )
    
    # Validate patient_id exists and belongs to clinic
    patient = db.query(Patient).filter(Patient.id == request.patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate doctor_id exists and belongs to clinic
    doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id, Doctor.clinic_id == clinic.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Validate service_id exists and belongs to clinic (if provided)
    if request.service_id is not None:
        service = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
    
    # Check for conflicting appointments with the same doctor
    # An appointment conflicts if:
    # 1. Same doctor_id
    # 2. Time ranges overlap (new_start < existing_end AND new_end > existing_start)
    # 3. Status is SCHEDULED, CONFIRMED, or PENDING_SYNC (not CANCELLED, RESCHEDULED, COMPLETED, NO_SHOW)
    conflicting_appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.doctor_id == request.doctor_id,
        Appointment.status.in_([
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.PENDING_SYNC,
            AppointmentStatus.PENDING
        ]),
        # Check for time overlap: new_start < existing_end AND new_end > existing_start
        Appointment.start_time < end_time_dt,
        Appointment.end_time > start_time_dt
    ).all()
    
    if conflicting_appointments:
        conflict_details = []
        for apt in conflicting_appointments:
            conflict_details.append({
                "appointment_id": apt.id,
                "start_time": apt.start_time.isoformat(),
                "end_time": apt.end_time.isoformat(),
                "patient_id": apt.patient_id,
                "status": apt.status.value
            })
        
        logger.warning(
            f"Appointment conflict detected for doctor_id {request.doctor_id} "
            f"at {start_time_dt.isoformat()} - {end_time_dt.isoformat()}. "
            f"Found {len(conflicting_appointments)} conflicting appointment(s)."
        )
        
        raise HTTPException(
            status_code=409,  # Conflict status code
            detail={
                "error": "Appointment conflict",
                "message": f"Doctor already has an appointment scheduled during this time slot.",
                "requested_time": {
                    "start_time": start_time_dt.isoformat(),
                    "end_time": end_time_dt.isoformat()
                },
                "conflicting_appointments": conflict_details
            }
        )
    
    # 1. Create appointment in database
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=request.patient_id,
        doctor_id=request.doctor_id,
        service_id=request.service_id,
        start_time=start_time_dt,
        end_time=end_time_dt,
        reason_note=request.reason,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Schedule SMS confirmation (background; configurable delay)
    if patient.phone:
        try:
            tz = pytz.timezone(clinic.timezone or "America/Edmonton")
            start_local = start_time_dt.astimezone(tz) if start_time_dt.tzinfo else tz.localize(start_time_dt)
            date_str = start_local.strftime("%Y-%m-%d")
            time_str = start_local.strftime("%I:%M %p")
            patient_name = " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"
            svc = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first() if request.service_id else None
            service_name = (svc.name if svc else None) or request.service_name
            background_tasks.add_task(
                send_booking_sms_delayed,
                patient.phone,
                patient_name,
                date_str,
                time_str,
                doctor.name,
                service_name,
                clinic.name,
            )
        except Exception as e:
            logger.warning("SMS confirmation skipped: %s", e)
    else:
        logger.info("No patient phone; skipping SMS confirmation")

    return AppointmentResponse(
        appointment_id=appointment.id,
        calendar_event_id=None,
        calendar_link=None,
        status=appointment.status.value,
    )
@app.get("/api/patients", response_model=List[PatientResponse])
async def list_patients(
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List patients with optional filters."""
    query = db.query(Patient).filter(Patient.clinic_id == clinic.id)
    if phone:
        query = query.filter(Patient.phone == phone)
    if email:
        query = query.filter(Patient.email == email)
    patients = query.all()
    return [PatientResponse.model_validate(p) for p in patients]


@app.post("/api/patients/verify", response_model=PatientVerifyResponse)
async def verify_patient(
    request: PatientVerifyRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Verify patient identity by phone number and date of birth.
    
    This is a secure endpoint that only returns patient_id if verification succeeds.
    No other patient data is exposed. Returns 404 if verification fails.
    
    Args:
        request: PatientVerifyRequest with phone and dob
    
    Returns:
        PatientVerifyResponse with patient_id if verification succeeds
        Raises 404 if no patient matches or verification fails
    """
    try:
        # Normalize phone to digits only
        phone_digits = ''.join(c for c in request.phone if c.isdigit())
        
        # Parse DOB
        from datetime import date as date_type
        dob_date = datetime.strptime(request.dob, '%Y-%m-%d').date()
        
        # Query patient by phone (scoped to clinic)
        patient = db.query(Patient).filter(Patient.phone == phone_digits, Patient.clinic_id == clinic.id).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify DOB matches
        if not patient.dob:
            raise HTTPException(status_code=404, detail="Patient verification failed")
        
        # Compare DOB (handle both date and string formats)
        patient_dob = patient.dob
        if isinstance(patient_dob, str):
            patient_dob = datetime.strptime(patient_dob, '%Y-%m-%d').date()
        
        if patient_dob != dob_date:
            raise HTTPException(status_code=404, detail="Patient verification failed")
        
        # Verification successful - return only patient_id
        return PatientVerifyResponse(patient_id=patient.id, verified=True)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}. Use YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying patient: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during verification")


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create new patient."""
    try:
        # Convert Pydantic model to dict
        patient_dict = patient_data.model_dump(exclude_none=True)
        
        # Convert dob string to date if provided
        if 'dob' in patient_dict and patient_dict['dob']:
            from datetime import date as date_type
            if isinstance(patient_dict['dob'], str):
                patient_dict['dob'] = datetime.strptime(patient_dict['dob'], '%Y-%m-%d').date()
        
        patient = Patient(clinic_id=clinic.id, **patient_dict)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return PatientResponse.model_validate(patient)
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = str(e)
        print(f"Error creating patient: {error_detail}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {error_detail}")


@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: dict,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.clinic_id == clinic.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in patient_data.items():
        if hasattr(patient, key):
            setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return PatientResponse.model_validate(patient)


# ============================================================================
# Database CRUD Endpoints - Appointments
# ============================================================================

@app.get("/api/appointments", response_model=List[AppointmentDetailResponse])
async def list_appointments(
    appointment_id: Optional[str] = Query(None, description="Filter by specific appointment ID"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, CANCELLED, COMPLETED, NO_SHOW, PENDING)"),
    start_date: Optional[str] = Query(None, description="Filter appointments starting from this date (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter appointments ending before this date (ISO format: YYYY-MM-DD)"),
    start_datetime: Optional[str] = Query(None, description="Filter appointments starting from this datetime (ISO format)"),
    end_datetime: Optional[str] = Query(None, description="Filter appointments ending before this datetime (ISO format)"),
    date: Optional[str] = Query(None, description="Filter appointments on a specific date (ISO format: YYYY-MM-DD)"),
    doctor_name: Optional[str] = Query(None, description="Filter by doctor name (e.g., 'Dr. Smith')"),
    patient_name: Optional[str] = Query(None, description="Filter by patient name (searches first_name and last_name)"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    List appointments with comprehensive filtering options.
    
    Supports filtering by:
    - appointment_id: Get specific appointment
    - patient_id: All appointments for a patient
    - doctor_id: All appointments for a doctor
    - service_id: All appointments for a service
    - status: Filter by appointment status
    - start_date/end_date: Date range filtering
    - start_datetime/end_datetime: Datetime range filtering
    - date: Appointments on a specific date
    - doctor_name: Filter by doctor name
    - patient_name: Filter by patient name (partial match)
    """
    query = db.query(Appointment).filter(Appointment.clinic_id == clinic.id)

    # Filter by appointment ID (returns single result if found)
    if appointment_id:
        query = query.filter(Appointment.id == appointment_id)
    
    # Filter by patient ID
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    
    # Filter by doctor ID
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    
    # Filter by service ID
    if service_id:
        query = query.filter(Appointment.service_id == service_id)
    
    # Filter by status
    if status:
        try:
            status_enum = AppointmentStatus(status.upper())
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid values: SCHEDULED, CANCELLED, COMPLETED, NO_SHOW, PENDING")
    
    # Filter by doctor name (scoped to clinic)
    if doctor_name:
        doctor = db.query(Doctor).filter(Doctor.clinic_id == clinic.id, Doctor.name.ilike(f"%{doctor_name}%")).first()
        if doctor:
            query = query.filter(Appointment.doctor_id == doctor.id)
        else:
            # Return empty list if doctor not found
            return []
    
    # Filter by patient name (scoped to clinic)
    if patient_name:
        patients = db.query(Patient).filter(
            Patient.clinic_id == clinic.id,
            (Patient.first_name.ilike(f"%{patient_name}%")) |
            (Patient.last_name.ilike(f"%{patient_name}%"))
        ).all()
        if patients:
            patient_ids = [p.id for p in patients]
            query = query.filter(Appointment.patient_id.in_(patient_ids))
        else:
            # Return empty list if no patients found
            return []
    
    # Date range filtering
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Appointment.start_time >= datetime.combine(start_dt, datetime.min.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Appointment.end_time <= datetime.combine(end_dt, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    # Datetime range filtering (more precise)
    if start_datetime:
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            query = query.filter(Appointment.start_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_datetime format. Use ISO format")
    
    if end_datetime:
        try:
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            query = query.filter(Appointment.end_time <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_datetime format. Use ISO format")
    
    # Filter by specific date
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            query = query.filter(
                Appointment.start_time >= start_of_day,
                Appointment.start_time <= end_of_day
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    appointments = query.order_by(Appointment.start_time).all()
    return [AppointmentDetailResponse(
        id=apt.id,
        patient_id=apt.patient_id,
        doctor_id=apt.doctor_id,
        service_id=apt.service_id,
        start_time=apt.start_time,
        end_time=apt.end_time,
        reason_note=apt.reason_note,
        status=apt.status.value,
        calendar_event_id=apt.calendar_event_id
    ) for apt in appointments]


@app.get("/api/appointments/{appointment_id}", response_model=AppointmentDetailResponse)
async def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get appointment by ID."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return AppointmentDetailResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        service_id=appointment.service_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        reason_note=appointment.reason_note,
        status=appointment.status.value,
        calendar_event_id=appointment.calendar_event_id
    )


@app.post("/api/appointments", response_model=AppointmentResponse)
async def create_appointment(
    request: AppointmentCreateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create appointment (also creates calendar event)."""
    return await create_calendar_event(request, db, clinic)


@app.put("/api/appointments/{appointment_id}", response_model=AppointmentDetailResponse)
async def update_appointment(
    appointment_id: str,
    updates: dict,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update appointment in database."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for key, value in updates.items():
        if hasattr(appointment, key):
            if key in ["start_time", "end_time"]:
                setattr(
                    appointment,
                    key,
                    datetime.fromisoformat(value.replace("Z", "+00:00")),
                )
            else:
                setattr(appointment, key, value)

    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    return AppointmentDetailResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        service_id=appointment.service_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        reason_note=appointment.reason_note,
        status=appointment.status.value,
        calendar_event_id=appointment.calendar_event_id
    )


@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Delete appointment permanently from database.
    Use PUT /api/appointments/{id}/cancel if you want to cancel but keep the record.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    try:
        db.delete(appointment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete appointment from database: {str(e)}",
        )

    return {
        "message": "Appointment deleted successfully",
        "appointment_id": appointment_id,
    }


@app.put("/api/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Cancel appointment (marks as CANCELLED but keeps record).
    Use DELETE endpoint if you want to permanently remove the appointment.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    # Schedule cancellation SMS (background; configurable delay)
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id, Patient.clinic_id == clinic.id).first()
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id, Doctor.clinic_id == clinic.id).first()
    if patient and patient.phone and doctor:
        try:
            tz = pytz.timezone(clinic.timezone or "America/Edmonton")
            start_local = appointment.start_time.astimezone(tz) if appointment.start_time.tzinfo else tz.localize(appointment.start_time)
            date_str = start_local.strftime("%Y-%m-%d")
            time_str = start_local.strftime("%I:%M %p")
            patient_name = " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"
            background_tasks.add_task(
                send_cancellation_sms_delayed,
                patient.phone,
                patient_name,
                date_str,
                time_str,
                doctor.name,
                clinic.name,
            )
        except Exception as e:
            logger.warning("Cancellation SMS skipped: %s", e)
    elif patient and not patient.phone:
        logger.info("No patient phone; skipping cancellation SMS")

    return AppointmentDetailResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        service_id=appointment.service_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        reason_note=appointment.reason_note,
        status=appointment.status.value,
        calendar_event_id=appointment.calendar_event_id
    )


@app.put("/api/appointments/{appointment_id}/status", response_model=AppointmentDetailResponse)
async def update_appointment_status(
    appointment_id: str,
    request: AppointmentStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update appointment status in database."""
    try:
        new_status = AppointmentStatus(request.status.upper())
    except ValueError:
        valid_statuses = [s.value for s in AppointmentStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Valid values: {', '.join(valid_statuses)}",
        )

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = new_status
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)
    
    return AppointmentDetailResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        service_id=appointment.service_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        reason_note=appointment.reason_note,
        status=appointment.status.value,
        calendar_event_id=appointment.calendar_event_id
    )


@app.put("/api/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Reschedule an existing appointment.
    Creates a new appointment with the new time/date and marks the old one as RESCHEDULED.
    """
    old_appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.clinic_id == clinic.id).first()
    if not old_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if old_appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reschedule appointment with status {old_appointment.status.value}. Only SCHEDULED appointments can be rescheduled.",
        )

    try:
        new_start_time = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        new_end_time = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))

        conflicting_appointments = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.doctor_id == request.doctor_id,
            Appointment.id != appointment_id,
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.PENDING_SYNC,
                AppointmentStatus.PENDING,
            ]),
            Appointment.start_time < new_end_time,
            Appointment.end_time > new_start_time,
        ).all()

        if conflicting_appointments:
            conflict_details = [
                {
                    "appointment_id": apt.id,
                    "start_time": apt.start_time.isoformat(),
                    "end_time": apt.end_time.isoformat(),
                    "patient_id": apt.patient_id,
                    "status": apt.status.value,
                }
                for apt in conflicting_appointments
            ]
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Appointment conflict",
                    "message": "Doctor already has an appointment scheduled during the requested time slot.",
                    "requested_time": {
                        "start_time": new_start_time.isoformat(),
                        "end_time": new_end_time.isoformat(),
                    },
                    "conflicting_appointments": conflict_details,
                },
            )

        new_appointment = Appointment(
            clinic_id=clinic.id,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            service_id=request.service_id,
            start_time=new_start_time,
            end_time=new_end_time,
            reason_note=request.reason,
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(new_appointment)
        db.flush()

        old_appointment.status = AppointmentStatus.RESCHEDULED
        old_appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(new_appointment)
        db.refresh(old_appointment)

        # Schedule reschedule confirmation SMS (background; configurable delay)
        patient = db.query(Patient).filter(Patient.id == request.patient_id, Patient.clinic_id == clinic.id).first()
        doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id, Doctor.clinic_id == clinic.id).first()
        svc = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first() if request.service_id else None
        service_name = (svc.name if svc else None) or request.service_name
        if patient and patient.phone and doctor:
            try:
                tz = pytz.timezone(clinic.timezone or "America/Edmonton")
                new_local = new_start_time.astimezone(tz) if new_start_time.tzinfo else tz.localize(new_start_time)
                date_str = new_local.strftime("%Y-%m-%d")
                time_str = new_local.strftime("%I:%M %p")
                patient_name = " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"
                background_tasks.add_task(
                    send_reschedule_sms_delayed,
                    patient.phone,
                    patient_name,
                    date_str,
                    time_str,
                    doctor.name,
                    service_name,
                    clinic.name,
                )
            except Exception as e:
                logger.warning("Reschedule SMS skipped: %s", e)
        elif patient and not patient.phone:
            logger.info("No patient phone; skipping reschedule SMS")

        return {
            "old_appointment_id": old_appointment.id,
            "new_appointment_id": new_appointment.id,
            "status": "RESCHEDULED",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rescheduling appointment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error rescheduling appointment: {str(e)}")


# ============================================================================
# Database CRUD Endpoints - Doctors
# ============================================================================

@app.get("/api/doctors")
async def list_doctors(
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List all doctors."""
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic.id, Doctor.is_active == True).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get doctor by ID."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.clinic_id == clinic.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"id": doctor.id, "name": doctor.name, "specialty": doctor.specialty, "is_active": doctor.is_active}


# ============================================================================
# Database CRUD Endpoints - Services
# ============================================================================

@app.get("/api/services")
async def list_services(
    name: Optional[str] = Query(None, description="Filter by service name"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List all services."""
    query = db.query(Service).filter(Service.clinic_id == clinic.id)
    if name:
        query = query.filter(Service.name.ilike(f"%{name}%"))
    services = query.all()
    return [{
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "duration_min": s.duration_min,
        "base_price": float(s.base_price) if s.base_price else None
    } for s in services]


@app.get("/api/services/{service_id}")
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get service by ID."""
    service = db.query(Service).filter(Service.id == service_id, Service.clinic_id == clinic.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "duration_min": service.duration_min,
        "base_price": float(service.base_price) if service.base_price else None
    }


# ============================================================================
# Health Check
# ============================================================================

@app.delete("/api/appointments/bulk/date/{date}")
async def delete_appointments_by_date_endpoint(
    date: str,
    dry_run: bool = Query(False, description="If true, only preview without deleting"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """
    Delete all appointments for a specific date from database.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2025-12-22")
        dry_run: If true, only return what would be deleted without actually deleting
    """
    try:
        target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-22)",
        )

    tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    start_of_day = tz.localize(datetime.combine(target_date_obj, datetime.min.time()))
    end_of_day = tz.localize(datetime.combine(target_date_obj, datetime.max.time()))

    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.start_time >= start_of_day,
        Appointment.start_time <= end_of_day,
    ).all()

    if not appointments:
        return {
            "message": f"No appointments found for {date}",
            "date": date,
            "appointments_found": 0,
            "deleted": 0,
        }

    if dry_run:
        return {
            "message": f"DRY RUN: Would delete {len(appointments)} appointment(s) for {date}",
            "date": date,
            "appointments_found": len(appointments),
            "appointments": [
                {
                    "id": apt.id,
                    "patient_id": apt.patient_id,
                    "doctor_id": apt.doctor_id,
                    "start_time": apt.start_time.isoformat(),
                    "status": apt.status.value,
                }
                for apt in appointments
            ],
            "deleted": 0,
        }

    deleted_count = 0
    failed_count = 0
    deleted_ids = []
    failed_ids = []

    for appointment in appointments:
        appointment_id = appointment.id
        try:
            db.delete(appointment)
            db.commit()
            deleted_count += 1
            deleted_ids.append(appointment_id)
        except Exception as e:
            db.rollback()
            failed_count += 1
            failed_ids.append(appointment_id)
            logger.warning(f"Failed to delete appointment {appointment_id}: {e}")

    return {
        "message": f"Deleted {deleted_count} appointment(s) for {date}",
        "date": date,
        "appointments_found": len(appointments),
        "deleted": deleted_count,
        "failed": failed_count,
        "deleted_ids": deleted_ids,
        "failed_ids": failed_ids,
    }


# ============================================================================
# Database CRUD Endpoints - Leads
# ============================================================================

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Create new lead."""
    try:
        lead_dict = lead_data.model_dump(exclude_none=True)
        lead = Lead(clinic_id=clinic.id, **lead_dict)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return LeadResponse.model_validate(lead)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {str(e)}")


@app.get("/api/leads", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List leads with optional filters."""
    query = db.query(Lead).filter(Lead.clinic_id == clinic.id)
    if status:
        try:
            status_enum = LeadStatus(status.upper())
            query = query.filter(Lead.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if source:
        query = query.filter(Lead.source == source)
    leads = query.order_by(Lead.created_at.desc()).all()
    return [LeadResponse.model_validate(lead) for lead in leads]


@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Get lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@app.put("/api/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = lead_data.model_dump(exclude_none=True)
    
    # Handle status update
    if "status" in update_data:
        try:
            status_enum = LeadStatus(update_data["status"].upper())
            lead.status = status_enum
            del update_data["status"]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data['status']}")
    
    # Update other fields
    for key, value in update_data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@app.put("/api/leads/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: str,
    request: LeadStatusUpdateRequest,
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """Update lead status."""
    try:
        new_status = LeadStatus(request.status.upper())
    except ValueError:
        valid_statuses = [s.value for s in LeadStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Valid values: {', '.join(valid_statuses)}"
        )
    
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.clinic_id == clinic.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = new_status
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


# ============================================================================
# Clinic Endpoints (multi-tenant)
# ============================================================================

class ClinicCreateRequest(BaseModel):
    """Request model for creating clinic."""
    id: str = Field(..., description="Clinic ID (e.g. clinic-a)")
    name: str = Field(..., description="Clinic display name")
    timezone: Optional[str] = Field("America/Edmonton", description="Timezone (e.g. America/Edmonton)")
    working_hour_start: Optional[int] = Field(9, description="Start of working hours (0-23)")
    working_hour_end: Optional[int] = Field(17, description="End of working hours (0-23)")


class ClinicResponse(BaseModel):
    """Response model for clinic config."""
    id: str
    name: str
    timezone: Optional[str] = None
    working_hour_start: Optional[int] = None
    working_hour_end: Optional[int] = None

    class Config:
        from_attributes = True


@app.post("/api/clinics", response_model=ClinicResponse)
async def create_clinic(
    request: ClinicCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new clinic (admin/setup)."""
    existing = db.query(Clinic).filter(Clinic.id == request.id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Clinic already exists: {request.id}")
    clinic = Clinic(
        id=request.id,
        name=request.name,
        timezone=request.timezone or "America/Edmonton",
        working_hour_start=request.working_hour_start or 9,
        working_hour_end=request.working_hour_end or 17,
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@app.get("/api/clinics/me", response_model=ClinicResponse)
async def get_clinic_me(clinic: Clinic = Depends(get_clinic)):
    """Get current clinic config (from X-Clinic-Id header)."""
    return ClinicResponse.model_validate(clinic)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/debug/db-info")
async def debug_db_info(db: Session = Depends(get_db)):
    """
    Debug: which database we're connected to and doctor count.
    Use this to verify Railway is hitting the same Supabase as the dashboard.
    """
    from database.connection import engine
    url = engine.url
    # Safe to expose: host and db name only (no password)
    db_host = url.host if hasattr(url, "host") else ("sqlite" if "sqlite" in str(url) else "unknown")
    db_name = url.database if hasattr(url, "database") else None
    doctor_count = db.query(Doctor).count()
    return {
        "database_host": db_host,
        "database_name": db_name,
        "doctor_count": doctor_count,
    }



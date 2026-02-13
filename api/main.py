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

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db, init_db
from database.models import Patient, Appointment, Doctor, Service, AppointmentStatus, Lead, LeadStatus
from tools.calendar_tools import (
    view_available_slots, 
    create_new_event, 
    get_calendar_service,
    CalendarTokenError,
    validate_calendar_credentials,
    refresh_calendar_token
)
from tools.event_template import format_calendar_event, parse_calendar_event
from tools.doctor_calendars import get_calendar_id_for_doctor
from googleapiclient.errors import HttpError
import pytz
import logging

logger = logging.getLogger("dental-receptionist")

EDMONTON_TZ = pytz.timezone('America/Edmonton')


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


# ============================================================================
# Calendar Endpoints
# ============================================================================

@app.get("/api/calendar/slots")
async def get_calendar_slots(
    request: Request,
    start_datetime: str = Query(..., description="ISO datetime string"),
    end_datetime: str = Query(..., description="ISO datetime string"),
    doctor_id: Optional[int] = Query(None, description="Doctor ID for filtering (preferred over doctor_name)"),
    doctor_name: Optional[str] = Query(None, description="Doctor name for filtering (fallback if doctor_id not provided)"),
    db: Session = Depends(get_db)
):
    """
    Get available calendar slots for a datetime range.
    
    Note: Cancelled and rescheduled appointments are automatically excluded from busy slots:
    - Google Calendar events with status="cancelled" are filtered out
    - Events with title starting with "[CANCELLED]" are filtered out
    - Events with title starting with "[RESCHEDULED]" are filtered out
    - This ensures cancelled and rescheduled appointment time slots are shown as available
    """
    try:
        # Extract all query parameters as kwargs (excluding the required ones)
        query_params = dict(request.query_params)
        # Remove the required parameters
        query_params.pop("start_datetime", None)
        query_params.pop("end_datetime", None)
        query_params.pop("doctor_id", None)
        query_params.pop("doctor_name", None)
        
        # Build kwargs dict - prefer doctor_id over doctor_name
        kwargs = {}
        if doctor_id is not None:
            # Resolve doctor_id to doctor_name for calendar_tools
            doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
            if doctor:
                kwargs["doctor_name"] = doctor.name
            else:
                # Doctor not found - proceed without doctor filter
                pass
        elif doctor_name:
            kwargs["doctor_name"] = doctor_name
        kwargs.update(query_params)
        
        # Run synchronous function in thread pool to avoid blocking
        # Note: view_available_slots filters out cancelled events from Google Calendar
        # (events with status="cancelled" or title starting with "[CANCELLED]")
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: view_available_slots(start_datetime, end_datetime, **kwargs)
        )
        
        # Check if result indicates calendar service error
        if isinstance(result, str) and "Calendar service unavailable" in result:
            logger.warning(f"Calendar service unavailable: {result}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Calendar service unavailable",
                    "message": result,
                    "instructions": "Please check calendar token configuration or contact administrator"
                }
            )
        
        return {"slots": result}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        logger.error(f"Error in get_calendar_slots: {error_detail}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/calendar/events")
async def create_calendar_event(request: AppointmentCreateRequest, db: Session = Depends(get_db)):
    """Create appointment in both database and calendar."""
    import asyncio
    loop = asyncio.get_event_loop()
    
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
    
    # Validate patient_id exists
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate doctor_id exists
    doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Validate service_id exists (if provided)
    if request.service_id is not None:
        service = db.query(Service).filter(Service.id == request.service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
    
    # Check for conflicting appointments with the same doctor
    # An appointment conflicts if:
    # 1. Same doctor_id
    # 2. Time ranges overlap (new_start < existing_end AND new_end > existing_start)
    # 3. Status is SCHEDULED, CONFIRMED, or PENDING_SYNC (not CANCELLED, RESCHEDULED, COMPLETED, NO_SHOW)
    conflicting_appointments = db.query(Appointment).filter(
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
    
    # 1. Create appointment in database first (always succeeds)
    appointment = Appointment(
        patient_id=request.patient_id,
        doctor_id=request.doctor_id,
        service_id=request.service_id,
        start_time=start_time_dt,
        end_time=end_time_dt,
        reason_note=request.reason,
        status=AppointmentStatus.PENDING_SYNC  # Will update to SCHEDULED after calendar creation
    )
    db.add(appointment)
    db.flush()  # Get appointment.id
    
    calendar_event_id = None
    calendar_link = None
    calendar_error = None
    
    # 2. Try to create event in Google Calendar (may fail, but database is already saved)
    try:
        # Reuse doctor variable from validation above
        doctor_name = doctor.name if doctor else None
        calendar_id = get_calendar_id_for_doctor(doctor_name)
        
        # Format calendar event using template
        event_data = format_calendar_event(
            appointment_id=appointment.id,
            patient_name=request.patient_name,
            service_name=request.service_name,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            service_id=request.service_id or 0,
            reason=request.reason
        )
        
        # Run synchronous Google Calendar operations in thread pool
        # Catch ALL exceptions from get_calendar_service, not just CalendarTokenError
        try:
            calendar_service = await loop.run_in_executor(None, get_calendar_service)
        except (CalendarTokenError, Exception) as e:
            logger.error(f"Calendar service unavailable when creating event: {e}")
            calendar_error = str(e)
            # Continue without calendar - appointment saved with PENDING_SYNC status
        else:
            # Reuse pre-parsed datetime objects
            if start_time_dt.tzinfo is None:
                start_dt_edmonton = EDMONTON_TZ.localize(start_time_dt)
            else:
                start_dt_edmonton = start_time_dt.astimezone(EDMONTON_TZ)
            
            if end_time_dt.tzinfo is None:
                end_dt_edmonton = EDMONTON_TZ.localize(end_time_dt)
            else:
                end_dt_edmonton = end_time_dt.astimezone(EDMONTON_TZ)
            
            calendar_event = {
                "summary": event_data["summary"],
                "description": event_data["description"],
                "start": {
                    "dateTime": start_dt_edmonton.isoformat(),
                    "timeZone": str(EDMONTON_TZ),
                },
                "end": {
                    "dateTime": end_dt_edmonton.isoformat(),
                    "timeZone": str(EDMONTON_TZ),
                },
            }
            
            try:
                created_event = await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().insert(calendarId=calendar_id, body=calendar_event).execute()
                )
                calendar_event_id = created_event.get('id')
                calendar_link = created_event.get('htmlLink')
                appointment.calendar_event_id = calendar_event_id
                appointment.status = AppointmentStatus.SCHEDULED
                logger.info(f"Successfully created calendar event {calendar_event_id} for appointment {appointment.id}")
            except HttpError as e:
                logger.error(f"HTTP error creating calendar event: {e}", exc_info=True)
                calendar_error = f"Failed to create calendar event: {str(e)}"
                # Keep appointment with PENDING_SYNC status
            except Exception as e:
                logger.error(f"Unexpected error creating calendar event: {e}", exc_info=True)
                calendar_error = f"Unexpected error: {str(e)}"
                # Keep appointment with PENDING_SYNC status
    
    except Exception as e:
        logger.error(f"Error in calendar event creation flow: {e}", exc_info=True)
        calendar_error = str(e)
        # Continue - appointment is already saved
    
    # 3. Always commit database changes (appointment is saved regardless of calendar success)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit appointment to database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save appointment: {str(e)}")
    
    # 4. Return response (with warning if calendar failed)
    if calendar_error:
        logger.warning(
            f"Appointment {appointment.id} created in database but calendar sync failed: {calendar_error}. "
            f"Status set to PENDING_SYNC for retry."
        )
        return JSONResponse(
            status_code=207,  # Multi-Status - partial success
            content={
                "appointment_id": appointment.id,
                "calendar_event_id": calendar_event_id,
                "calendar_link": calendar_link,
                "status": appointment.status.value,
                "warning": "Appointment saved but calendar sync failed",
                "error": calendar_error,
                "message": "Appointment was created in database but could not be synced to Google Calendar. "
                          "It will be retried automatically or can be manually synced later."
            }
        )
    
    return AppointmentResponse(
        appointment_id=appointment.id,
        calendar_event_id=calendar_event_id,
        calendar_link=calendar_link,
        status=appointment.status.value
    )
@app.get("/api/patients", response_model=List[PatientResponse])
async def list_patients(
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List patients with optional filters."""
    query = db.query(Patient)
    if phone:
        query = query.filter(Patient.phone == phone)
    if email:
        query = query.filter(Patient.email == email)
    patients = query.all()
    return [PatientResponse.model_validate(p) for p in patients]


@app.post("/api/patients/verify", response_model=PatientVerifyResponse)
async def verify_patient(
    request: PatientVerifyRequest,
    db: Session = Depends(get_db)
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
        
        # Query patient by phone
        patient = db.query(Patient).filter(Patient.phone == phone_digits).first()
        
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
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(patient_data: PatientCreateRequest, db: Session = Depends(get_db)):
    """Create new patient."""
    try:
        # Convert Pydantic model to dict
        patient_dict = patient_data.model_dump(exclude_none=True)
        
        # Convert dob string to date if provided
        if 'dob' in patient_dict and patient_dict['dob']:
            from datetime import date as date_type
            if isinstance(patient_dict['dob'], str):
                patient_dict['dob'] = datetime.strptime(patient_dict['dob'], '%Y-%m-%d').date()
        
        patient = Patient(**patient_dict)
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
async def update_patient(patient_id: str, patient_data: dict, db: Session = Depends(get_db)):
    """Update patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
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
    db: Session = Depends(get_db)
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
    query = db.query(Appointment)
    
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
    
    # Filter by doctor name
    if doctor_name:
        doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
        if doctor:
            query = query.filter(Appointment.doctor_id == doctor.id)
        else:
            # Return empty list if doctor not found
            return []
    
    # Filter by patient name
    if patient_name:
        patients = db.query(Patient).filter(
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
async def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """Get appointment by ID."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
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
async def create_appointment(request: AppointmentCreateRequest, db: Session = Depends(get_db)):
    """Create appointment (also creates calendar event)."""
    # Reuse the calendar/events endpoint logic
    return await create_calendar_event(request)


@app.put("/api/appointments/{appointment_id}", response_model=AppointmentDetailResponse)
async def update_appointment(
    appointment_id: str,
    updates: dict,
    db: Session = Depends(get_db)
):
    """Update appointment (also updates calendar if calendar_event_id exists)."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update database fields
    for key, value in updates.items():
        if hasattr(appointment, key):
            if key in ['start_time', 'end_time']:
                setattr(appointment, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
            else:
                setattr(appointment, key, value)
    
    appointment.updated_at = datetime.utcnow()
    db.commit()
    
    # Update calendar event if calendar_event_id exists
    if appointment.calendar_event_id:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
            calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
            
            try:
                calendar_service = await loop.run_in_executor(None, get_calendar_service)
            except CalendarTokenError as e:
                logger.warning(f"Calendar service unavailable when updating appointment {appointment_id}: {e}")
                # Database update succeeded, calendar sync will be retried later
            else:
                # Get existing event
                event = await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().get(calendarId=calendar_id, eventId=appointment.calendar_event_id).execute()
                )
                
                # Update event times if changed
                if 'start_time' in updates or 'end_time' in updates:
                    start_dt = datetime.fromisoformat(updates.get('start_time', appointment.start_time.isoformat()).replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(updates.get('end_time', appointment.end_time.isoformat()).replace('Z', '+00:00'))
                    
                    if start_dt.tzinfo is None:
                        start_dt_edmonton = EDMONTON_TZ.localize(start_dt)
                    else:
                        start_dt_edmonton = start_dt.astimezone(EDMONTON_TZ)
                    
                    if end_dt.tzinfo is None:
                        end_dt_edmonton = EDMONTON_TZ.localize(end_dt)
                    else:
                        end_dt_edmonton = end_dt.astimezone(EDMONTON_TZ)
                    
                    event['start'] = {
                        "dateTime": start_dt_edmonton.isoformat(),
                        "timeZone": str(EDMONTON_TZ),
                    }
                    event['end'] = {
                        "dateTime": end_dt_edmonton.isoformat(),
                        "timeZone": str(EDMONTON_TZ),
                    }
                
                await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().update(calendarId=calendar_id, eventId=appointment.calendar_event_id, body=event).execute()
                )
        except HttpError as e:
            # Log error but don't fail the update - database is already updated
            logger.warning(f"Failed to update calendar event: {e}")
        except Exception as e:
            # Log error but don't fail the update - database is already updated
            logger.warning(f"Unexpected error updating calendar event: {e}", exc_info=True)
    
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
async def delete_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """
    Delete appointment completely from both database and calendar.
    
    This permanently removes the appointment. Use PUT /api/appointments/{id} with status=CANCELLED
    if you want to cancel but keep the record.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    calendar_event_id = appointment.calendar_event_id
    doctor_id = appointment.doctor_id
    
    # Delete from database first
    try:
        db.delete(appointment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete appointment from database: {str(e)}")
    
    # Delete from calendar if calendar_event_id exists
    if calendar_event_id:
        try:
            doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
            calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
            
            # Run synchronous Google Calendar operations in thread pool
            try:
                calendar_service = await loop.run_in_executor(None, get_calendar_service)
            except CalendarTokenError as e:
                logger.warning(f"Calendar service unavailable when deleting appointment {appointment_id}: {e}")
                # Appointment already deleted from DB, calendar sync will be skipped
            else:
                # Delete the calendar event
                await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().delete(
                        calendarId=calendar_id,
                        eventId=calendar_event_id
                    ).execute()
                )
                logger.info(f"✓ Calendar event {calendar_event_id} deleted successfully")
        except HttpError as e:
            # Log error but don't fail - appointment already deleted from DB
            logger.warning(f"Failed to delete calendar event {calendar_event_id}: {e}")
            logger.warning("  Appointment was deleted from database but calendar event may still exist.")
        except Exception as e:
            logger.warning(f"Error deleting calendar event: {e}", exc_info=True)
    
    return {
        "message": "Appointment deleted successfully",
        "appointment_id": appointment_id,
        "calendar_event_deleted": calendar_event_id is not None
    }


@app.put("/api/appointments/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """
    Cancel appointment (marks as CANCELLED but keeps record).
    
    Updates status to CANCELLED and marks calendar event as cancelled.
    Use DELETE endpoint if you want to permanently remove the appointment.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update status to CANCELLED
    appointment.status = AppointmentStatus.CANCELLED
    appointment.updated_at = datetime.utcnow()
    
    # Update calendar event to show cancelled
    if appointment.calendar_event_id:
        try:
            doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
            calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
            
            # Run synchronous Google Calendar operations in thread pool
            try:
                calendar_service = await loop.run_in_executor(None, get_calendar_service)
            except CalendarTokenError as e:
                logger.warning(f"Calendar service unavailable when cancelling appointment {appointment_id}: {e}")
                # Database update succeeded, calendar sync will be skipped
            else:
                # Get existing event
                event = await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().get(
                        calendarId=calendar_id,
                        eventId=appointment.calendar_event_id
                    ).execute()
                )
                
                # Update event title to show cancelled
                event['summary'] = f"[CANCELLED] {event.get('summary', '')}"
                
                await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().update(
                        calendarId=calendar_id,
                        eventId=appointment.calendar_event_id,
                        body=event
                    ).execute()
                )
        except HttpError as e:
            logger.warning(f"Failed to update calendar event: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error updating calendar event: {e}", exc_info=True)
    
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


@app.put("/api/appointments/{appointment_id}/status", response_model=AppointmentDetailResponse)
async def update_appointment_status(
    appointment_id: str,
    request: AppointmentStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update appointment status to any valid status value.
    
    Updates status in database and optionally updates calendar event based on status:
    - CANCELLED: Adds [CANCELLED] prefix to event title
    - CONFIRMED: Adds [CONFIRMED] prefix to event title
    - REMINDER_SENT: Adds [REMINDER SENT] prefix to event title
    - Other statuses: Only updates database, no calendar changes
    
    Args:
        appointment_id: ID of the appointment to update
        request: AppointmentStatusUpdateRequest with status field
    
    Returns:
        AppointmentDetailResponse with updated appointment details
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    # Validate status enum
    try:
        new_status = AppointmentStatus(request.status.upper())
    except ValueError:
        valid_statuses = [s.value for s in AppointmentStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Valid values: {', '.join(valid_statuses)}"
        )
    
    # Get appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update status in database
    appointment.status = new_status
    appointment.updated_at = datetime.utcnow()
    
    # Update calendar event based on status type
    if appointment.calendar_event_id:
        # Statuses that affect calendar visibility
        status_prefixes = {
            AppointmentStatus.CANCELLED: "[CANCELLED]",
            AppointmentStatus.CONFIRMED: "[CONFIRMED]",
            AppointmentStatus.REMINDER_SENT: "[REMINDER SENT]"
        }
        
        if new_status in status_prefixes:
            try:
                doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
                calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
                
                # Run synchronous Google Calendar operations in thread pool
                try:
                    calendar_service = await loop.run_in_executor(None, get_calendar_service)
                except CalendarTokenError as e:
                    logger.warning(f"Calendar service unavailable when updating appointment status {appointment_id}: {e}")
                    # Database update succeeded, calendar sync will be skipped
                else:
                    # Get existing event
                    event = await loop.run_in_executor(
                        None,
                        lambda: calendar_service.events().get(
                            calendarId=calendar_id,
                            eventId=appointment.calendar_event_id
                        ).execute()
                    )
                    
                    # Remove any existing status prefixes
                    summary = event.get('summary', '')
                    for prefix in status_prefixes.values():
                        if summary.startswith(prefix):
                            summary = summary[len(prefix):].strip()
                    
                    # Add new prefix
                    prefix = status_prefixes[new_status]
                    event['summary'] = f"{prefix} {summary}"
                    
                    # Update event
                    await loop.run_in_executor(
                        None,
                        lambda: calendar_service.events().update(
                            calendarId=calendar_id,
                            eventId=appointment.calendar_event_id,
                            body=event
                        ).execute()
                    )
            except HttpError as e:
                logger.warning(f"Failed to update calendar event: {e}")
            except Exception as e:
                logger.warning(f"Error updating calendar event: {e}", exc_info=True)
    
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
    db: Session = Depends(get_db)
):
    """
    Reschedule an existing appointment.
    
    This creates a new appointment with the new time/date and marks the old one as RESCHEDULED.
    Both database and calendar are updated synchronously.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    # Get the old appointment
    old_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not old_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if old_appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reschedule appointment with status {old_appointment.status.value}. Only SCHEDULED appointments can be rescheduled."
        )
    
    try:
        # Parse new start/end times
        new_start_time = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
        new_end_time = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
        
        # Check for conflicting appointments with the same doctor (excluding the old appointment)
        conflicting_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == request.doctor_id,
            Appointment.id != appointment_id,  # Exclude the appointment being rescheduled
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.PENDING_SYNC,
                AppointmentStatus.PENDING
            ]),
            # Check for time overlap: new_start < existing_end AND new_end > existing_start
            Appointment.start_time < new_end_time,
            Appointment.end_time > new_start_time
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
                f"Reschedule conflict detected for doctor_id {request.doctor_id} "
                f"at {new_start_time.isoformat()} - {new_end_time.isoformat()}. "
                f"Found {len(conflicting_appointments)} conflicting appointment(s)."
            )
            
            raise HTTPException(
                status_code=409,  # Conflict status code
                detail={
                    "error": "Appointment conflict",
                    "message": f"Doctor already has an appointment scheduled during the requested time slot.",
                    "requested_time": {
                        "start_time": new_start_time.isoformat(),
                        "end_time": new_end_time.isoformat()
                    },
                    "conflicting_appointments": conflict_details
                }
            )
        
        # Create new appointment in database first
        new_appointment = Appointment(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            service_id=request.service_id,
            start_time=new_start_time,
            end_time=new_end_time,
            reason_note=request.reason,
            status=AppointmentStatus.SCHEDULED
        )
        db.add(new_appointment)
        db.flush()  # Get the ID
        
        # Initialize variables
        calendar_service = None
        calendar_link = None
        
        # Create calendar event for new appointment
        try:
            doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
            calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
            
            # Run synchronous Google Calendar operations in thread pool
            try:
                calendar_service = await loop.run_in_executor(None, get_calendar_service)
            except CalendarTokenError as e:
                logger.error(f"Calendar service unavailable when rescheduling appointment: {e}")
                new_appointment.status = AppointmentStatus.PENDING_SYNC
                calendar_link = None
            else:
                # Format event using template
                event_data = format_calendar_event(
                    appointment_id=new_appointment.id,
                    patient_name=request.patient_name,
                    service_name=request.service_name,
                    patient_id=request.patient_id,
                    doctor_id=request.doctor_id,
                    service_id=request.service_id or 0,
                    reason=request.reason
                )
                
                # Convert times to Edmonton timezone
                edmonton_tz = pytz.timezone('America/Edmonton')
                if new_start_time.tzinfo is None:
                    new_start_edmonton = edmonton_tz.localize(new_start_time)
                else:
                    new_start_edmonton = new_start_time.astimezone(edmonton_tz)
                
                if new_end_time.tzinfo is None:
                    new_end_edmonton = edmonton_tz.localize(new_end_time)
                else:
                    new_end_edmonton = new_end_time.astimezone(edmonton_tz)
                
                event = {
                    "summary": event_data["summary"],
                    "description": event_data["description"],
                    "start": {
                        "dateTime": new_start_edmonton.isoformat(),
                        "timeZone": str(edmonton_tz),
                    },
                    "end": {
                        "dateTime": new_end_edmonton.isoformat(),
                        "timeZone": str(edmonton_tz),
                    },
                }
                
                try:
                    created_event = await loop.run_in_executor(
                        None,
                        lambda: calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
                    )
                    
                    new_appointment.calendar_event_id = created_event.get('id')
                    new_appointment.status = AppointmentStatus.SCHEDULED
                    calendar_link = created_event.get('htmlLink', '')
                except HttpError as e:
                    logger.error(f"Error creating calendar event for rescheduled appointment: {e}")
                    new_appointment.status = AppointmentStatus.PENDING_SYNC
                    calendar_link = None
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}", exc_info=True)
            new_appointment.status = AppointmentStatus.PENDING_SYNC
            calendar_link = None
        
        # Mark old appointment as RESCHEDULED
        old_appointment.status = AppointmentStatus.RESCHEDULED
        old_appointment.updated_at = datetime.utcnow()
        
        # Update old calendar event to show rescheduled (optional - can mark as cancelled or update title)
        if old_appointment.calendar_event_id and calendar_service:
            try:
                old_doctor = db.query(Doctor).filter(Doctor.id == old_appointment.doctor_id).first()
                old_calendar_id = get_calendar_id_for_doctor(old_doctor.name if old_doctor else None)
                
                # Use the same calendar_service instance
                # Get existing event
                old_event = await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().get(
                        calendarId=old_calendar_id,
                        eventId=old_appointment.calendar_event_id
                    ).execute()
                )
                
                # Update event title to show rescheduled
                old_event['summary'] = f"[RESCHEDULED] {old_event.get('summary', '')}"
                
                await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().update(
                        calendarId=old_calendar_id,
                        eventId=old_appointment.calendar_event_id,
                        body=old_event
                    ).execute()
                )
            except HttpError as e:
                logger.warning(f"Warning: Failed to update old calendar event: {e}")
        
        db.commit()
        db.refresh(new_appointment)
        db.refresh(old_appointment)
        
        return {
            "old_appointment_id": old_appointment.id,
            "new_appointment_id": new_appointment.id,
            "calendar_event_id": new_appointment.calendar_event_id,
            "calendar_link": calendar_link if new_appointment.calendar_event_id else None,
            "status": "RESCHEDULED"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error rescheduling appointment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error rescheduling appointment: {str(e)}")


# ============================================================================
# Database CRUD Endpoints - Doctors
# ============================================================================

@app.get("/api/doctors")
async def list_doctors(db: Session = Depends(get_db)):
    """List all doctors."""
    doctors = db.query(Doctor).filter(Doctor.is_active == True).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Get doctor by ID."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"id": doctor.id, "name": doctor.name, "specialty": doctor.specialty, "is_active": doctor.is_active}


# ============================================================================
# Database CRUD Endpoints - Services
# ============================================================================

@app.get("/api/services")
async def list_services(
    name: Optional[str] = Query(None, description="Filter by service name"),
    db: Session = Depends(get_db)
):
    """List all services."""
    query = db.query(Service)
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
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
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
    db: Session = Depends(get_db)
):
    """
    Delete all appointments for a specific date from both database and calendar.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., "2025-12-22")
        dry_run: If true, only return what would be deleted without actually deleting
    
    Returns:
        Summary of deletion operation
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    try:
        target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-22)")
    
    # Calculate start and end of day in Edmonton timezone
    start_of_day = EDMONTON_TZ.localize(datetime.combine(target_date_obj, datetime.min.time()))
    end_of_day = EDMONTON_TZ.localize(datetime.combine(target_date_obj, datetime.max.time()))
    
    # Query appointments for the date
    appointments = db.query(Appointment).filter(
        Appointment.start_time >= start_of_day,
        Appointment.start_time <= end_of_day
    ).all()
    
    if not appointments:
        return {
            "message": f"No appointments found for {date}",
            "date": date,
            "appointments_found": 0,
            "deleted": 0
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
                    "calendar_event_id": apt.calendar_event_id
                }
                for apt in appointments
            ],
            "deleted": 0
        }
    
    # Actually delete
    deleted_count = 0
    failed_count = 0
    calendar_deleted_count = 0
    calendar_failed_count = 0
    deleted_ids = []
    failed_ids = []
    
    # Get calendar service
    calendar_service = None
    try:
        calendar_service = await loop.run_in_executor(None, get_calendar_service)
    except CalendarTokenError as e:
        logger.warning(f"Calendar service unavailable for bulk delete: {e}")
        # Continue with database deletion only
    except Exception as e:
        logger.warning(f"Could not initialize Google Calendar service: {e}", exc_info=True)
    
    for appointment in appointments:
        appointment_id = appointment.id
        calendar_event_id = appointment.calendar_event_id
        
        # Delete from calendar first (if calendar_event_id exists)
        calendar_deleted = False
        if calendar_event_id and calendar_service:
            try:
                doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
                calendar_id = get_calendar_id_for_doctor(doctor.name if doctor else None)
                
                await loop.run_in_executor(
                    None,
                    lambda: calendar_service.events().delete(
                        calendarId=calendar_id,
                        eventId=calendar_event_id
                    ).execute()
                )
                calendar_deleted = True
                calendar_deleted_count += 1
            except Exception as e:
                calendar_failed_count += 1
                print(f"Warning: Failed to delete calendar event {calendar_event_id}: {e}")
        
        # Delete from database
        try:
            db.delete(appointment)
            db.commit()
            deleted_count += 1
            deleted_ids.append(appointment_id)
        except Exception as e:
            db.rollback()
            failed_count += 1
            failed_ids.append(appointment_id)
            print(f"Error: Failed to delete appointment {appointment_id} from database: {e}")
    
    return {
        "message": f"Deleted {deleted_count} appointment(s) for {date}",
        "date": date,
        "appointments_found": len(appointments),
        "deleted": deleted_count,
        "failed": failed_count,
        "calendar_deleted": calendar_deleted_count,
        "calendar_failed": calendar_failed_count,
        "deleted_ids": deleted_ids,
        "failed_ids": failed_ids
    }


# ============================================================================
# Database CRUD Endpoints - Leads
# ============================================================================

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreateRequest, db: Session = Depends(get_db)):
    """Create new lead."""
    try:
        lead_dict = lead_data.model_dump(exclude_none=True)
        lead = Lead(**lead_dict)
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
    db: Session = Depends(get_db)
):
    """List leads with optional filters."""
    query = db.query(Lead)
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
async def get_lead(lead_id: str, db: Session = Depends(get_db)):
    """Get lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@app.put("/api/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
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
    db: Session = Depends(get_db)
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
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = new_status
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# ============================================================================
# Admin Endpoints - Token Management
# ============================================================================

@app.get("/api/admin/calendar/validate")
async def validate_calendar_token():
    """
    Validate calendar credentials (admin endpoint).
    
    Returns status of calendar token and instructions if invalid.
    """
    is_valid, error_message = validate_calendar_credentials()
    
    if is_valid:
        return {
            "status": "valid",
            "message": "Calendar credentials are valid"
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "invalid",
                "error": error_message,
                "instructions": (
                    "To fix calendar token issues:\n"
                    "1. Delete the token.json file\n"
                    "2. Run the OAuth flow manually (requires user interaction):\n"
                    "   from tools.calendar_tools import get_calendar_service\n"
                    "   service = get_calendar_service()  # This will open browser\n"
                    "3. Or use a script that runs OAuth flow interactively"
                )
            }
        )


@app.post("/api/admin/calendar/refresh")
async def refresh_calendar_token_endpoint():
    """
    Manually trigger calendar token refresh (admin endpoint).
    
    Useful for recovery when tokens expire.
    """
    success, message = refresh_calendar_token()
    
    if success:
        return {
            "status": "success",
            "message": message
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "failed",
                "error": message,
                "instructions": (
                    "Token refresh failed. To fix:\n"
                    "1. Delete the token.json file\n"
                    "2. Run the OAuth flow manually (requires user interaction):\n"
                    "   from tools.calendar_tools import get_calendar_service\n"
                    "   service = get_calendar_service()  # This will open browser\n"
                    "3. Or use a script that runs OAuth flow interactively"
                )
            }
        )

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
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session, joinedload

from database.connection import init_db
from database.models import Patient, Appointment, Provider, Service, AppointmentStatus, Lead, LeadStatus, Clinic, DEFAULT_CLINIC_ID
import json as _json
from tools.slot_utils import get_available_slots

# Re-exports — historical home of these helpers. v2 routers and tests
# import them from api.main; keep the names available here.
from api.dependencies import get_db, get_clinic_id, get_clinic  # noqa: F401
from api.serializers import _busy_block_envelope, _to_appointment_detail  # noqa: F401

from clients.sms_client import (
    send_booking_sms_delayed,
    send_cancellation_sms_delayed,
    send_reschedule_sms_delayed,
)
from clients.email_client import resolve_booking_notification_recipient, send_clinic_booking_email_delayed
import pytz
import logging

# Re-export appointment schemas so existing callers that import from api.main keep working.
from api.v1.appointments.schemas import (  # noqa: F401
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentStatusUpdateRequest,
    AppointmentDetailResponse,
)

logger = logging.getLogger("dental-receptionist")

EDMONTON_TZ = pytz.timezone('America/Edmonton')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    try:
        init_db()
        logger.info("Database tables ready")
    except Exception as e:
        logger.warning("Database init failed: %s", e)
    try:
        from database.connection import engine as _engine
        from database.observability import register_sql_events
        register_sql_events(_engine)
    except Exception as e:
        logger.warning("SQL observability not registered: %s", e)
    # Start Track 3 reminder scheduler
    _reminder_task = None
    try:
        from api.v2.scheduling.reminder_scheduler import start_reminder_scheduler
        from database.connection import get_db as _get_db
        _reminder_task = start_reminder_scheduler(_get_db)
    except Exception as _e:
        logger.warning("Reminder scheduler not started: %s", _e)
    yield
    # Shutdown: cancel reminder scheduler
    if _reminder_task is not None:
        try:
            from api.v2.scheduling.reminder_scheduler import stop_reminder_scheduler
            stop_reminder_scheduler()
        except Exception:
            pass


app = FastAPI(
    title="Dental Clinic Calendar API",
    description="API for calendar and database operations",
    version="1.0.0",
    lifespan=lifespan
)

# Observability middleware (request tracing, structured logging) - registered BEFORE CORS
from api.middleware.observability import ObservabilityMiddleware
app.add_middleware(ObservabilityMiddleware)

# CORS: allow frontend (Vite often on 5173 or 5174 when 5173 is in use)
_CORS_BASE = [
    "http://localhost:5173", "http://localhost:5174", "http://localhost:3000",
    "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:3000",
    "https://dental-crm--rockyridgeai-dental.us-central1.hosted.app",
]
_CORS_EXTRA = [o.strip() for o in os.getenv("CORS_EXTRA_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_BASE + _CORS_EXTRA,
    # Allow any Firebase App Hosting URL for this project — covers preview
    # channels and region renames without code changes.
    allow_origin_regex=r"https://[a-z0-9-]+--rockyridgeai-dental\.[a-z0-9-]+\.hosted\.app",
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
    provider_id: Optional[int] = Query(None, description="Provider ID for filtering"),
    provider_name: Optional[str] = Query(None, description="Provider name for filtering"),
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
            provider_id=provider_id,
            provider_name=provider_name,
            slot_minutes=slot_minutes,
            clinic_id=clinic.id,
            timezone_str=clinic.timezone,
            hour_start=clinic.working_hour_start,
            hour_end=clinic.working_hour_end,
        )
        return slots
    except Exception as e:
        logger.error(f"Error in get_calendar_slots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/events")
async def list_calendar_events(
    start: Optional[str] = Query(None, description="ISO start of range (inclusive)"),
    end: Optional[str] = Query(None, description="ISO end of range (exclusive)"),
    db: Session = Depends(get_db),
    clinic: Clinic = Depends(get_clinic),
):
    """List appointments in [start, end) as FullCalendar-style event objects."""
    q = db.query(Appointment).filter(Appointment.clinic_id == clinic.id)
    if start:
        try:
            q = q.filter(Appointment.start_time >= datetime.fromisoformat(start.replace("Z", "+00:00")))
        except ValueError:
            raise HTTPException(400, f"Invalid start datetime: {start}")
    if end:
        try:
            q = q.filter(Appointment.start_time < datetime.fromisoformat(end.replace("Z", "+00:00")))
        except ValueError:
            raise HTTPException(400, f"Invalid end datetime: {end}")
    out = []
    for appt in q.order_by(Appointment.start_time.asc()).all():
        out.append({
            "id": appt.id,
            "title": (appt.notes or "Appointment")[:60],
            "start": appt.start_time.isoformat() if appt.start_time else None,
            "end": appt.end_time.isoformat() if appt.end_time else None,
            "status": appt.status.value if hasattr(appt.status, "value") else str(appt.status),
            "patient_id": appt.patient_id,
            "provider_id": appt.provider_id,
        })
    return out


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
    
    # Validate provider_id exists and belongs to clinic
    provider = db.query(Provider).filter(
        Provider.id == request.provider_id, Provider.clinic_id == clinic.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Validate service_id exists and belongs to clinic (if provided)
    if request.service_id is not None:
        service = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
    
    # Check for conflicting appointments with the same provider
    # An appointment conflicts if:
    # 1. Same provider_id
    # 2. Time ranges overlap (new_start < existing_end AND new_end > existing_start)
    # 3. Status is SCHEDULED, CONFIRMED, or PENDING_SYNC (not CANCELLED, RESCHEDULED, COMPLETED, NO_SHOW)
    conflicting_appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.provider_id == request.provider_id,
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
            f"Appointment conflict detected for provider_id {request.provider_id} "
            f"at {start_time_dt.isoformat()} - {end_time_dt.isoformat()}. "
            f"Found {len(conflicting_appointments)} conflicting appointment(s)."
        )
        
        raise HTTPException(
            status_code=409,  # Conflict status code
            detail={
                "error": "Appointment conflict",
                "message": "Provider already has an appointment scheduled during this time slot.",
                "requested_time": {
                    "start_time": start_time_dt.isoformat(),
                    "end_time": end_time_dt.isoformat()
                },
                "conflicting_appointments": conflict_details
            }
        )

    # Reject overlap with the provider's recurring busy blocks (lunch, hospital
    # rounds, admin time, etc.). Slot listing already hides these — this guard
    # closes the loop for direct API calls / stale UI tabs.
    from tools.slot_utils import find_busy_block_overlap as _find_busy_overlap
    _busy_tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    _busy_block = _find_busy_overlap(db, clinic.id, request.provider_id, start_time_dt, end_time_dt, _busy_tz)
    if _busy_block is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Provider busy",
                "message": "Provider is on a busy block during this time slot.",
                "requested_time": {
                    "start_time": start_time_dt.isoformat(),
                    "end_time": end_time_dt.isoformat(),
                },
                "busy_block": _busy_block_envelope(_busy_block),
            },
        )

    # 1. Create appointment in database
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=request.patient_id,
        provider_id=request.provider_id,
        service_id=request.service_id,
        start_time=start_time_dt,
        end_time=end_time_dt,
        reason_note=request.reason,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    provider_display_name = " ".join(filter(None, [provider.title, provider.name])).strip() or provider.name
    tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    start_local = start_time_dt.astimezone(tz) if start_time_dt.tzinfo else tz.localize(start_time_dt)
    date_str = start_local.strftime("%Y-%m-%d")
    time_str = start_local.strftime("%I:%M %p")
    patient_name = " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"
    svc = db.query(Service).filter(Service.id == request.service_id, Service.clinic_id == clinic.id).first() if request.service_id else None
    service_name = (svc.name if svc else None) or request.service_name

    # Schedule SMS confirmation (background; configurable delay)
    if patient.phone:
        try:
            background_tasks.add_task(
                send_booking_sms_delayed,
                patient.phone,
                patient_name,
                date_str,
                time_str,
                provider_display_name,
                service_name,
                clinic.name,
                clinic.address,
                clinic.contact_phone,
            )
        except Exception as e:
            logger.warning("SMS confirmation skipped: %s", e)
    else:
        logger.info("No patient phone; skipping SMS confirmation")

    booking_notify_to = resolve_booking_notification_recipient(clinic.booking_notification_email)
    if booking_notify_to:
        try:
            when_local = f"{date_str} at {time_str}"
            background_tasks.add_task(
                send_clinic_booking_email_delayed,
                booking_notify_to,
                clinic.name,
                appointment.id,
                patient_name,
                patient.phone or "",
                patient.email or "",
                when_local,
                provider_display_name,
                service_name,
            )
        except Exception as e:
            logger.warning("Clinic booking email skipped: %s", e)

    # SSE: notify any subscribed CRM clients (in-process; no-op if no
    # subscribers). Wrapped in try/except so a bus failure can NEVER
    # poison the booking response — the appointment is already committed
    # by this point.
    try:
        from api.v2.events import publish_appointment_created
        publish_appointment_created(clinic.id, {
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "patient_name": patient_name,
            "provider_id": appointment.provider_id,
            "provider_name": provider_display_name,
            "service_id": appointment.service_id,
            "service_name": service_name,
            "start_time": appointment.start_time.isoformat(),
            "end_time": appointment.end_time.isoformat(),
            "start_time_local": f"{date_str} {time_str}",
            "status": appointment.status.value,
        })
    except Exception as e:
        logger.warning("SSE publish_appointment_created failed: %s", e)

    return AppointmentResponse(
        appointment_id=appointment.id,
        calendar_event_id=None,
        calendar_link=None,
        status=appointment.status.value,
    )





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
    Debug: which database we're connected to and provider count.
    Use this to verify Railway is hitting the same Supabase as the dashboard.
    """
    from database.connection import engine
    url = engine.url
    # Safe to expose: host and db name only (no password)
    db_host = url.host if hasattr(url, "host") else ("sqlite" if "sqlite" in str(url) else "unknown")
    db_name = url.database if hasattr(url, "database") else None
    provider_count = db.query(Provider).count()
    return {
        "database_host": db_host,
        "database_name": db_name,
        "provider_count": provider_count,
    }


# ============================================================================
# v1 routers — historical /api/* paths; contract preserved for dental-agent.
# Intentionally NOT wrapped in try/except: a missing v1 router would silently
# break the contract dental-agent depends on, so it must be a hard failure.
# ============================================================================
from api.v1.clinics.router import router as _v1_clinics_router
app.include_router(_v1_clinics_router)
from api.v1.providers.router import router as _v1_providers_router
app.include_router(_v1_providers_router)
from api.v1.catalog.router import router as _v1_catalog_router
app.include_router(_v1_catalog_router)
from api.v1.leads.router import router as _v1_leads_router
app.include_router(_v1_leads_router)
from api.v1.patients.router import router as _v1_patients_router
app.include_router(_v1_patients_router)
from api.v1.appointments.router import router as _v1_appointments_router
app.include_router(_v1_appointments_router)

# ============================================================================
# v2 routers (Track 1 — Auth / RBAC / Audit)
# ============================================================================
try:
    from api.v2.auth.router import router as _auth_router
    from api.v2.admin.router import router as _admin_router
    from database.auth.audit import register_audit_listeners
    app.include_router(_auth_router)
    app.include_router(_admin_router)
    register_audit_listeners()
except ImportError:
    pass  # v2 modules not yet present — v1 keeps working


# ============================================================================
# v2 routers (Track 2 — Clinical / Lab / Treatment Plans)
# ============================================================================
try:
    import database.clinical.models  # noqa: F401 — register models with Base
    from api.v2.clinical.router import router as _clinical_router
    from api.v2.lab.router import router as _lab_router
    from api.v2.treatment_plans.router import router as _tp_router
    app.include_router(_clinical_router)
    app.include_router(_lab_router)
    # Mount treatment plans at both hyphenated and underscore paths
    app.include_router(_tp_router, prefix="/api/v2/treatment-plans")
    app.include_router(_tp_router, prefix="/api/v2/treatment_plans")
except ImportError:
    pass  # v2 clinical modules not yet present


# ============================================================================
# v2 routers (Track 3 — Scheduling / Billing / Insurance / Comms / CRM)
# ============================================================================
try:
    import database.ops.models  # noqa: F401 — register models with Base
    from api.v2.scheduling.router import router as _scheduling_router
    from api.v2.billing.router import router as _billing_router
    from api.v2.insurance.router import router as _insurance_router
    from api.v2.communications.router import router as _comms_router
    from api.v2.crm.router import router as _crm_router
    app.include_router(_scheduling_router)
    app.include_router(_billing_router)
    app.include_router(_insurance_router)
    app.include_router(_comms_router)
    app.include_router(_crm_router)
except ImportError:
    pass  # v2 ops modules not yet present

# v2 routers (F0 — Settings)
try:
    from api.v2.settings.router import router as _settings_router
    app.include_router(_settings_router)
except ImportError:
    pass

# v2 routers (Reporting — Dashboard KPIs)
try:
    from api.v2.reporting.router import router as _reporting_router
    app.include_router(_reporting_router)
except ImportError:
    pass

# v2 routers (Events — Server-Sent Events for CRM live updates)
try:
    from api.v2.events import router as _events_router
    app.include_router(_events_router)
except ImportError:
    pass

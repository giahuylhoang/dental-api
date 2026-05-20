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
from api.v1.calendar.router import router as _v1_calendar_router
app.include_router(_v1_calendar_router)

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

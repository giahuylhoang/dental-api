# dental-api v1 Router Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `api/main.py` (1,678 lines, 32 v1 routes, inline schemas, inline business logic) into a domain-organized router layout mirroring `api/v2/`, with **zero externally observable behavior change**.

**Architecture:** Per-domain `api/v1/<domain>/router.py` + `schemas.py`. Shared deps in `api/dependencies.py`, shared serializers in `api/serializers.py`. Complex logic (appointment conflict detection, background notifications, slot wrapping) extracted to `services/`. `main.py` becomes ~150-line app assembly. Re-exports preserve `from api.main import get_clinic` for 14 v2 routers + tests that already import it.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, uv. Python 3.11+.

**Spec:** `docs/superpowers/specs/2026-05-19-v1-router-refactor-design.md`

**The gate:** `uv run pytest tests/test_contract_v1.py tests/test_api.py -q` MUST be green at the start of every task and at the end of every task. If a task makes it red, revert that task; do not move on.

**Important inherited constraint:** 14 v2 routers and many tests `from api.main import get_clinic` (or `get_clinic_id`, `app`). The plumbing task introduces `api/dependencies.py` as the new home, but `main.py` continues to re-export the names so nothing else breaks. Do not touch v2 imports in this refactor.

---

## Task 0: Baseline + branch setup

**Files:**
- Read-only: `tests/test_contract_v1.py`, `tests/test_api.py`, `api/main.py`

- [ ] **Step 1: Confirm working directory and branch**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git status
git rev-parse --abbrev-ref HEAD
```

Expected: clean working tree (no uncommitted changes), some branch name. If the branch is `main` or a feature branch unrelated to this work, create a dedicated branch:

```bash
git checkout -b refactor/v1-router-split
```

If already on a refactor branch from the brainstorming session (`pms-frontend-overhaul`), stay on it.

- [ ] **Step 2: Establish baseline test pass**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: all tests pass. If anything fails before the refactor starts, stop and fix it before continuing — the gate has to be green before you can use it as a gate.

- [ ] **Step 3: Snapshot the OpenAPI spec for later diff**

```bash
uv run python -c "import json; from api.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))" > /tmp/openapi-before.json
wc -l /tmp/openapi-before.json
```

Expected: a non-empty JSON file (typically several thousand lines). Keep `/tmp/openapi-before.json` around for Task 13.

- [ ] **Step 4: Confirm the route inventory hasn't drifted from the spec**

```bash
grep -cE '@app\.(get|post|put|delete|patch)' api/main.py
```

Expected: `32`. If you see a different number, list the routes (`grep -nE '@app\.(get|post|put|delete|patch)' api/main.py`) and reconcile with the spec before continuing.

---

## Task 1: Extract shared dependencies + serializers

**Files:**
- Create: `api/dependencies.py`
- Create: `api/serializers.py`
- Modify: `api/main.py` (remove the originals, re-export the names)

**What moves:**
- `get_clinic_id` (`api/main.py:69`)
- `get_clinic` (`api/main.py:74`)
- `_busy_block_envelope` (`api/main.py:26`)
- `_to_appointment_detail` (`api/main.py:201`)

- [ ] **Step 1: Create `api/dependencies.py`**

```python
"""Shared FastAPI dependencies for the v1 API surface.

These were inlined in api/main.py historically. They are re-exported from
api.main for backwards-compatibility with v2 routers and tests that do
`from api.main import get_clinic`.
"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID


def get_clinic_id(request: Request) -> str:
    """Resolve the active clinic id from the X-Clinic-Id header.

    Falls back to DEFAULT_CLINIC_ID when the header is absent.
    """
    return request.headers.get("X-Clinic-Id", DEFAULT_CLINIC_ID)


def get_clinic(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_clinic_id),
) -> Clinic:
    """Resolve and return the active Clinic row, 404 if it doesn't exist."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail=f"Clinic '{clinic_id}' not found")
    return clinic


__all__ = ["get_db", "get_clinic_id", "get_clinic"]
```

> Compare against `api/main.py:69-82` and **copy the body verbatim** if it differs from the snippet above. The snippet is the expected shape, not authoritative — `api/main.py` is. Preserve any side behavior (logging, header normalization) the existing code has.

- [ ] **Step 2: Create `api/serializers.py`**

```python
"""Shared serializers used by multiple v1 routers.

Pure functions that transform ORM rows into Pydantic / dict shapes.
"""
from __future__ import annotations

import json as _json

from database.models import Appointment

# AppointmentDetailResponse is defined in api/v1/appointments/schemas.py
# once Task 6/Task 11 has run. Until then it lives in api/main.py and is
# imported below at call time to avoid an import cycle during the
# step-by-step migration.


def _busy_block_envelope(block) -> dict:
    """Build the 409 'Provider busy' detail.busy_block payload.

    Surfaces both the legacy single-day fields (`weekday`) and the v2 fields
    (`weekdays`, `specific_date`, `recurrence_until`) so consumers can pattern
    on either shape.
    """
    weekdays_list = None
    raw = getattr(block, "weekdays", None)
    if raw:
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, list):
                weekdays_list = [int(x) for x in parsed]
        except (ValueError, TypeError):
            weekdays_list = None
    # ... rest of body verbatim from api/main.py:26-67
    raise NotImplementedError("Replace with the verbatim body from api/main.py:26-67")


def _to_appointment_detail(apt: Appointment):
    """Build an AppointmentDetailResponse from an Appointment ORM row.

    Imports the Pydantic class lazily to avoid an import cycle while v1
    appointment schemas still live in api.main.
    """
    from api.main import AppointmentDetailResponse  # noqa: WPS433 (intentional lazy import)
    # ... rest of body verbatim from api/main.py:201-220
    raise NotImplementedError("Replace with the verbatim body from api/main.py:201-220")


__all__ = ["_busy_block_envelope", "_to_appointment_detail"]
```

> The `NotImplementedError` lines are placeholders telling you what to copy — the engineer must replace them with the verbatim bodies from `api/main.py`. The body of `_to_appointment_detail` references `AppointmentDetailResponse`; keep the **lazy import** until Task 6 moves the schema out of `main.py`. After Task 6, you can flip it to a top-level import.

- [ ] **Step 3: Update `api/main.py` to import-and-re-export**

In `api/main.py`, delete the four function bodies (`_busy_block_envelope`, `get_clinic_id`, `get_clinic`, `_to_appointment_detail`) and replace with:

```python
# Re-exports — historical home of these helpers. v2 routers and tests
# import them from api.main; keep the names available here.
from api.dependencies import get_db, get_clinic_id, get_clinic  # noqa: F401
from api.serializers import _busy_block_envelope, _to_appointment_detail  # noqa: F401
```

Place the re-export block near the top, immediately after the existing `database.*` and `tools.*` imports so the names are bound before any `@app.<verb>` decorator references them.

- [ ] **Step 4: Run the gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py tests/test_observability.py -q
```

Expected: all pass. If `from api.main import get_clinic` fails in any v2 router, your re-export is missing — fix it before continuing.

- [ ] **Step 5: Run the full suite**

```bash
uv run pytest -q
```

Expected: same number of passes as the baseline from Task 0 Step 2. Any new failures = this task regressed something.

- [ ] **Step 6: Commit**

```bash
git add api/dependencies.py api/serializers.py api/main.py
git commit -m "refactor(api): extract shared deps + serializers from main.py

Move get_clinic_id, get_clinic, _busy_block_envelope, and
_to_appointment_detail to api/dependencies.py and api/serializers.py.
main.py re-exports the names so 14 v2 routers and tests that do
'from api.main import get_clinic' keep working unchanged."
```

---

## Task 2: Move `clinics/` domain

**Files:**
- Create: `api/v1/__init__.py` (empty)
- Create: `api/v1/clinics/__init__.py` (empty)
- Create: `api/v1/clinics/schemas.py`
- Create: `api/v1/clinics/router.py`
- Modify: `api/main.py` (delete the 3 clinics routes + 3 Pydantic models; add `include_router`)

**Routes moving** (per `api/main.py:1490-1583`):
- `POST   /api/clinics`
- `GET    /api/clinics/me`
- `PATCH  /api/clinics/me`

**Pydantic models moving:** `ClinicCreateRequest`, `ClinicResponse`, `ClinicUpdateRequest`.

- [ ] **Step 1: Create the v1 package marker**

```bash
mkdir -p api/v1/clinics
touch api/v1/__init__.py api/v1/clinics/__init__.py
```

- [ ] **Step 2: Create `api/v1/clinics/schemas.py`**

Copy `ClinicCreateRequest`, `ClinicResponse`, `ClinicUpdateRequest` verbatim from `api/main.py:1490-1530` into `api/v1/clinics/schemas.py`. Keep imports minimal:

```python
"""Pydantic schemas for /api/clinics."""
from typing import Optional
from pydantic import BaseModel, ConfigDict


# --- paste class bodies verbatim from api/main.py:1490-1530 ---
```

- [ ] **Step 3: Create `api/v1/clinics/router.py`**

```python
"""v1 clinics router — /api/clinics, /api/clinics/me."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic
from api.v1.clinics.schemas import (
    ClinicCreateRequest,
    ClinicResponse,
    ClinicUpdateRequest,
)

router = APIRouter(tags=["clinics"])


# --- paste route bodies verbatim from api/main.py:1532-1583 ---
# Change every `@app.<verb>(...)` to `@router.<verb>(...)` —
# leave the path strings, response_models, and bodies untouched.
```

- [ ] **Step 4: Mount the router in `api/main.py`**

Find the block where v2 routers are mounted (`app.include_router(_auth_router)` etc. starting around `api/main.py:1617`). Above that block, add:

```python
# v1 routers — historical /api/* paths; preserved for dental-agent.
from api.v1.clinics.router import router as _v1_clinics_router
app.include_router(_v1_clinics_router)
```

- [ ] **Step 5: Delete originals from `api/main.py`**

Delete:
- `ClinicCreateRequest`, `ClinicResponse`, `ClinicUpdateRequest` classes (was `api/main.py:1490-1530`)
- The three `@app.<verb>("/api/clinics...")` route functions (was `api/main.py:1532-1583`)

- [ ] **Step 6: Run the gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'clinic or Clinic'
```

Expected: all clinic tests pass.

- [ ] **Step 7: Run full v1 + v2 contract**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py tests/test_observability.py -q
```

Expected: green.

- [ ] **Step 8: Commit**

```bash
git add api/v1/__init__.py api/v1/clinics/ api/main.py
git commit -m "refactor(api): move v1 clinics routes to api/v1/clinics/"
```

---

## Task 3: Move `providers/` domain

**Files:**
- Create: `api/v1/providers/__init__.py`
- Create: `api/v1/providers/router.py`
- Modify: `api/main.py`

**Routes moving** (per `api/main.py`):
- `GET /api/doctors` (line 355 — legacy alias, still in use)
- `GET /api/providers` (line 1190)
- `GET /api/providers/{provider_id}` (line 1211)

No Pydantic schemas to move (these endpoints return plain dicts or use the Provider ORM model directly — confirm by reading the bodies first; if any inline `BaseModel` exists, move it into a `schemas.py`).

- [ ] **Step 1: Create the package and router**

```bash
mkdir -p api/v1/providers
touch api/v1/providers/__init__.py
```

Create `api/v1/providers/router.py`:

```python
"""v1 providers router — /api/providers and the /api/doctors legacy alias."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Provider

router = APIRouter(tags=["providers"])


# --- paste route bodies verbatim from api/main.py for: ---
#   @app.get("/api/doctors")           (api/main.py:355)
#   @app.get("/api/providers")         (api/main.py:1190)
#   @app.get("/api/providers/{provider_id}")  (api/main.py:1211)
# Change every `@app.<verb>(...)` to `@router.<verb>(...)`.
```

- [ ] **Step 2: Mount in `api/main.py`**

Below the clinics mount from Task 2:

```python
from api.v1.providers.router import router as _v1_providers_router
app.include_router(_v1_providers_router)
```

- [ ] **Step 3: Delete originals from `api/main.py`**

Remove the three route functions.

- [ ] **Step 4: Run the gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'provider or doctor'
```

Expected: pass.

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add api/v1/providers/ api/main.py
git commit -m "refactor(api): move v1 providers (+ /api/doctors alias) to api/v1/providers/"
```

---

## Task 4: Move `catalog/` domain (services-the-resource)

**Files:**
- Create: `api/v1/catalog/__init__.py`
- Create: `api/v1/catalog/router.py`
- Modify: `api/main.py`

> Folder is `catalog`, not `services`, to avoid colliding with the top-level `services/` package introduced in later tasks.

**Routes moving:**
- `GET /api/services` (line 1236)
- `GET /api/services/{service_id}` (line 1256)

- [ ] **Step 1: Create the router**

```bash
mkdir -p api/v1/catalog
touch api/v1/catalog/__init__.py
```

`api/v1/catalog/router.py`:

```python
"""v1 service catalog router — /api/services and /api/services/{id}.

Domain folder is `catalog/` to avoid colliding with the top-level
services/ package.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Service

router = APIRouter(tags=["services"])


# --- paste @app.get("/api/services") and @app.get("/api/services/{service_id}")
#     verbatim from api/main.py:1236-1278; rename decorators to @router. ---
```

- [ ] **Step 2: Mount + delete originals + run gate + commit**

Mount in `api/main.py`:

```python
from api.v1.catalog.router import router as _v1_catalog_router
app.include_router(_v1_catalog_router)
```

Delete originals (`api/main.py:1236-1278`).

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'service or Service'
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

```bash
git add api/v1/catalog/ api/main.py
git commit -m "refactor(api): move v1 service catalog routes to api/v1/catalog/"
```

---

## Task 5: Move `leads/` domain

**Files:**
- Create: `api/v1/leads/__init__.py`
- Create: `api/v1/leads/schemas.py`
- Create: `api/v1/leads/router.py`
- Modify: `api/main.py`

**Pydantic moving:** `LeadCreateRequest` (`api/main.py:141`), `LeadUpdateRequest` (line 150), `LeadResponse` (line 160), `LeadStatusUpdateRequest` (line 176).

**Routes moving:**
- `POST /api/leads` (line 1370)
- `GET  /api/leads` (line 1390)
- `GET  /api/leads/{lead_id}` (line 1411)
- `PUT  /api/leads/{lead_id}` (line 1424)
- `PUT  /api/leads/{lead_id}/status` (line 1458)

- [ ] **Step 1: Create schemas.py with the four lead Pydantic models**

Copy verbatim. Top of file:

```python
"""Pydantic schemas for /api/leads."""
from typing import Optional
from pydantic import BaseModel, ConfigDict
# ... add only the imports the copied classes actually use
```

- [ ] **Step 2: Create router.py**

```python
"""v1 leads router — /api/leads CRUD + status."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Lead, LeadStatus
from api.v1.leads.schemas import (
    LeadCreateRequest, LeadUpdateRequest, LeadResponse, LeadStatusUpdateRequest,
)

router = APIRouter(tags=["leads"])

# --- paste the five route bodies verbatim; rename to @router. ---
```

- [ ] **Step 3: Mount + delete originals + run gate + commit**

Mount in `api/main.py`:

```python
from api.v1.leads.router import router as _v1_leads_router
app.include_router(_v1_leads_router)
```

Delete originals (Pydantic models at `api/main.py:141-180` and routes at `1370-1489`).

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'lead or Lead'
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

```bash
git add api/v1/leads/ api/main.py
git commit -m "refactor(api): move v1 leads routes to api/v1/leads/"
```

---

## Task 6: Move `patients/` domain

**Files:**
- Create: `api/v1/patients/__init__.py`
- Create: `api/v1/patients/schemas.py`
- Create: `api/v1/patients/router.py`
- Modify: `api/main.py`
- Modify: `api/serializers.py` (flip the lazy `AppointmentDetailResponse` import to top-level — but only AFTER Task 11 moves it; do **not** touch it in this task)

**Pydantic moving:** `PatientCreateRequest` (`api/main.py:103`), `PatientResponse` (line 117), `PatientVerifyRequest` (line 129), `PatientVerifyResponse` (line 135).

**Routes moving:**
- `GET  /api/patients` (line 582)
- `POST /api/patients/verify` (line 599)
- `GET  /api/patients/{patient_id}` (line 656)
- `POST /api/patients` (line 669)
- `PUT  /api/patients/{patient_id}` (line 700)

- [ ] **Step 1: schemas.py**

Copy the four Pydantic models verbatim.

- [ ] **Step 2: router.py**

```python
"""v1 patients router — /api/patients CRUD + /api/patients/verify."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Clinic, Patient
from api.v1.patients.schemas import (
    PatientCreateRequest, PatientResponse,
    PatientVerifyRequest, PatientVerifyResponse,
)

router = APIRouter(tags=["patients"])

# --- paste five route bodies verbatim; rename to @router. ---
# /api/patients/verify must come BEFORE /api/patients/{patient_id} so
# FastAPI doesn't match "verify" as a {patient_id} param.
```

- [ ] **Step 3: Mount + delete + gate + commit**

```python
from api.v1.patients.router import router as _v1_patients_router
app.include_router(_v1_patients_router)
```

Delete originals.

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'patient or Patient'
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

```bash
git add api/v1/patients/ api/main.py
git commit -m "refactor(api): move v1 patients routes to api/v1/patients/"
```

---

## Task 7: Extract `services/notifications.py`

**Files:**
- Create: `services/__init__.py` (empty file — converts the dir from leftover to real package)
- Create: `services/notifications.py`
- Modify: `api/main.py` (the calendar/appointments routes will reference these; this task only extracts, no route changes yet)

**What moves:** The functions that schedule `BackgroundTasks` for Twilio SMS + SMTP email, plus `resolve_booking_notification_recipient`. Currently inlined inside the appointment + calendar route handlers in `api/main.py`.

- [ ] **Step 1: Catalogue the notification call sites**

Before writing code, read the three handlers that schedule notifications:
- `POST /api/calendar/events` (`api/main.py:372`)
- `PUT /api/appointments/{id}/cancel` (`api/main.py:950`)
- `PUT /api/appointments/{id}/reschedule` (`api/main.py:1039`)

Find every place that calls `background_tasks.add_task(...)` or constructs SMS / email arguments, and note the inputs. Also find `resolve_booking_notification_recipient`.

- [ ] **Step 2: Create `services/__init__.py`**

```python
"""Business-logic services extracted from api/main.py during the v1 refactor.

Services own the multi-step orchestration that doesn't belong in a route
handler: conflict detection, status transitions, background-task scheduling.
"""
```

- [ ] **Step 3: Create `services/notifications.py`**

```python
"""Background-task scheduling for booking SMS + clinic email notifications.

All entry points accept a FastAPI BackgroundTasks instance so the injection
point stays at the router boundary. None of the functions in this module
may raise back to the caller — notifications are best-effort and logged
on failure (this preserves the v1 contract).
"""
import logging
import os
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from clients.email_client import send_booking_email  # adjust to actual symbol
from clients.sms_client import send_sms              # adjust to actual symbol
from database.models import Appointment, Clinic, Patient

logger = logging.getLogger(__name__)


def resolve_booking_notification_recipient(clinic: Clinic) -> Optional[str]:
    """Resolve the email address the clinic should be notified at.

    Priority: BOOKING_NOTIFICATION_TO env var (testing override) >
    clinic.booking_notification_email > None (no email sent).
    """
    env_override = os.getenv("BOOKING_NOTIFICATION_TO")
    if env_override:
        return env_override
    return getattr(clinic, "booking_notification_email", None)


def schedule_booking_notifications(
    background_tasks: BackgroundTasks,
    *,
    appointment: Appointment,
    patient: Patient,
    clinic: Clinic,
    db: Session,
) -> None:
    """Schedule SMS-to-patient + email-to-clinic for a new booking."""
    # --- paste the body that currently inlines this work
    #     inside POST /api/calendar/events (api/main.py:372ff). ---
    raise NotImplementedError("Copy verbatim from api/main.py:372 booking-notification block")


def schedule_cancel_notifications(
    background_tasks: BackgroundTasks,
    *,
    appointment: Appointment,
    patient: Patient,
    clinic: Clinic,
    db: Session,
) -> None:
    """Schedule cancellation notifications."""
    # --- paste from PUT /api/appointments/{id}/cancel (api/main.py:950ff). ---
    raise NotImplementedError("Copy verbatim from api/main.py:950 cancel-notification block")


def schedule_reschedule_notifications(
    background_tasks: BackgroundTasks,
    *,
    old_appointment: Appointment,
    new_appointment: Appointment,
    patient: Patient,
    clinic: Clinic,
    db: Session,
) -> None:
    """Schedule reschedule notifications."""
    # --- paste from PUT /api/appointments/{id}/reschedule (api/main.py:1039ff). ---
    raise NotImplementedError("Copy verbatim from api/main.py:1039 reschedule-notification block")
```

> The function signatures above are the **proposed** interface. After reading the real call sites, adjust signatures so they take exactly the values currently passed at the call sites — no more, no less. Avoid YAGNI parameters. If the existing code passes `tz` or `notify_phone` explicitly, accept those instead of re-deriving them.

- [ ] **Step 4: Inline call swap is in Task 11, not here**

This task is extract-only. The route handlers in `api/main.py` still inline the work for now. We swap them in Task 11 when we move the appointments router.

- [ ] **Step 5: Run gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green (we changed nothing externally — only added new files).

- [ ] **Step 6: Commit**

```bash
git add services/__init__.py services/notifications.py
git commit -m "refactor(api): extract notification scheduling to services/notifications.py

No call sites updated yet — the routes in api/main.py still inline this
work. Swap-in happens when calendar/appointments routers move (Task 11)."
```

---

## Task 8: Extract `services/slots.py`

**Files:**
- Create: `services/slots.py`

**What moves:** A thin wrapper around `tools/slot_utils.get_available_slots` so the new `calendar/router.py` doesn't reach directly into `tools/`. This is one function.

- [ ] **Step 1: Read the current call site**

```bash
grep -n "get_available_slots" api/main.py tools/slot_utils.py
```

Note the parameters the route at `api/main.py:289` (`GET /api/calendar/slots`) passes.

- [ ] **Step 2: Create the wrapper**

`services/slots.py`:

```python
"""Slot-availability service — thin wrapper around tools.slot_utils.

Exists so routers can import from services/ instead of reaching into tools/.
No behavioral change vs. calling tools.slot_utils.get_available_slots
directly.
"""
from typing import List, Optional
from datetime import date as _date

from sqlalchemy.orm import Session

from tools.slot_utils import get_available_slots as _underlying


def get_available_slots(
    db: Session,
    *,
    clinic_id: str,
    target_date: _date,
    provider_id: Optional[int] = None,
    service_id: Optional[int] = None,
    duration_minutes: Optional[int] = None,
) -> List[dict]:
    """Compute available slots for a date.

    Delegates to tools.slot_utils. Keep the signature here aligned with the
    route handler's needs — adjust to match what api/main.py:289 actually
    passes today.
    """
    return _underlying(
        db,
        clinic_id=clinic_id,
        target_date=target_date,
        provider_id=provider_id,
        service_id=service_id,
        duration_minutes=duration_minutes,
    )
```

> Adjust the signature to match the **actual** kwargs the existing route passes — do not invent parameters. The principle here is "indirection, no transformation."

- [ ] **Step 3: Run gate + commit**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

```bash
git add services/slots.py
git commit -m "refactor(api): add services/slots.py wrapper around tools.slot_utils"
```

---

## Task 9: Extract `services/appointments.py`

**Files:**
- Create: `services/appointments.py`

**What moves:**
- Conflict detection against `ProviderBusyBlock` + active-status `Appointment` rows (currently duplicated at `api/main.py:319` and `api/main.py:916`)
- Status-transition validation for `PUT /api/appointments/{id}/status`
- Reschedule orchestration

- [ ] **Step 1: Diff the two conflict-detection blocks before writing anything**

```bash
sed -n '305,360p' api/main.py > /tmp/conflict_create.py
sed -n '900,950p' api/main.py > /tmp/conflict_reschedule.py
diff /tmp/conflict_create.py /tmp/conflict_reschedule.py
```

**Decision rule:** If the two blocks are byte-identical (modulo variable names), extract a single function that both call sites use. If they differ in meaningful ways (different status set, different time window math, different return shape), extract them as **two separate functions** that share helpers — do not silently unify behavior the routes currently produce.

Record which path you took in the commit message.

- [ ] **Step 2: Create `services/appointments.py`**

```python
"""Appointment business logic extracted from api/main.py.

- Conflict detection (shared by create + reschedule)
- Status transitions
- Reschedule orchestration (delete-old + create-new semantics)
- Bulk delete by date

The "active statuses" set used here MUST stay aligned with the set used
in tools/slot_utils for slot computation. If you change one, change both.
"""
from __future__ import annotations

from datetime import date as _date, datetime
from typing import Iterable, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database.models import (
    Appointment, AppointmentStatus, Clinic, Provider, ProviderBusyBlock,
)
from api.serializers import _busy_block_envelope

# Source of truth for "this appointment counts when checking for conflicts".
# Must match tools/slot_utils.
ACTIVE_STATUSES: tuple[AppointmentStatus, ...] = (
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.PENDING_SYNC,
    AppointmentStatus.PENDING,
)


def check_conflicts_for_create(
    db: Session, *, clinic: Clinic, provider_id: int, start: datetime, end: datetime,
) -> None:
    """Raise HTTPException(409) with the busy_block envelope if conflicting.

    Source: api/main.py:319 (POST /api/calendar/events + POST /api/appointments).
    """
    # --- paste body verbatim, adapting to use the ACTIVE_STATUSES constant. ---
    raise NotImplementedError("Copy from api/main.py:319 verbatim")


def check_conflicts_for_reschedule(
    db: Session, *, clinic: Clinic, provider_id: int, start: datetime, end: datetime,
    excluding_appointment_id: int,
) -> None:
    """Same as check_conflicts_for_create but ignores the appointment being moved.

    Source: api/main.py:916 (PUT /api/appointments/{id} and /reschedule).
    """
    # --- paste body verbatim if it differs from create-side; else have
    #     this function delegate to check_conflicts_for_create with an
    #     extra filter. The diff in Step 1 decides which.
    raise NotImplementedError("Copy from api/main.py:916 — see Step 1 decision")


def transition_status(
    db: Session, *, appointment: Appointment, new_status: AppointmentStatus,
) -> Appointment:
    """Apply a status transition with whatever validation main.py:1005 does today.

    Source: PUT /api/appointments/{id}/status (api/main.py:1005).
    """
    raise NotImplementedError("Copy from api/main.py:1005")


def reschedule(
    db: Session, *, clinic: Clinic, old_appointment: Appointment,
    new_start: datetime, new_end: datetime, **kwargs,
) -> Appointment:
    """Reschedule semantics from api/main.py:1039.

    Returns the new Appointment row. Caller is responsible for scheduling
    notifications (services.notifications.schedule_reschedule_notifications).
    """
    raise NotImplementedError("Copy from api/main.py:1039 — preserve cancel-old + create-new ordering")


def bulk_delete_by_date(
    db: Session, *, clinic: Clinic, target_date: _date, provider_id: Optional[int] = None,
) -> int:
    """Bulk-delete appointments for a date. Source: api/main.py:1279.

    Returns the count deleted.
    """
    raise NotImplementedError("Copy from api/main.py:1279")
```

> The signatures above are **proposals**. Adjust to match what the actual route handlers pass in today. Do not invent parameters.

- [ ] **Step 3: Run gate + commit**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green (nothing imports the new module yet).

```bash
git add services/appointments.py
git commit -m "refactor(api): extract appointment logic to services/appointments.py

Conflict detection, status transitions, reschedule orchestration, bulk
delete. Call sites updated in Task 11."
```

---

## Task 10: Move `appointments/` router

> Appointments moves **before** calendar because `POST /api/calendar/events` imports `AppointmentCreateRequest` / `AppointmentResponse`, which live in this task's `schemas.py`.

**Files:**
- Create: `api/v1/appointments/__init__.py`
- Create: `api/v1/appointments/schemas.py`
- Create: `api/v1/appointments/router.py`
- Modify: `api/main.py`
- Modify: `api/serializers.py` (flip lazy import to top-level — see Step 6)

**Pydantic moving:** `AppointmentCreateRequest` (`api/main.py:83`), `AppointmentResponse` (line 95), `AppointmentStatusUpdateRequest` (line 181), `AppointmentDetailResponse` (line 186).

**Routes moving** (in order — `/api/appointments/bulk/date/{date}` MUST come before any `/api/appointments/{id}/*` routes so FastAPI doesn't match "bulk" as an id):
- `GET    /api/appointments` (line 723)
- `DELETE /api/appointments/bulk/date/{date}` (line 1279) — declare before `{appointment_id}` routes
- `GET    /api/appointments/{appointment_id}` (line 857)
- `POST   /api/appointments` (line 875)
- `PUT    /api/appointments/{appointment_id}` (line 886)
- `DELETE /api/appointments/{appointment_id}` (line 920)
- `PUT    /api/appointments/{appointment_id}/cancel` (line 950)
- `PUT    /api/appointments/{appointment_id}/status` (line 1005)
- `PUT    /api/appointments/{appointment_id}/reschedule` (line 1039)

- [ ] **Step 1: schemas.py**

Copy the four Pydantic models verbatim into `api/v1/appointments/schemas.py`. Add the imports each class actually uses.

- [ ] **Step 2: router.py — the routes**

```python
"""v1 appointments router — /api/appointments and nested actions."""
from datetime import date as _date
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from api.dependencies import get_clinic, get_db
from api.serializers import _to_appointment_detail
from database.models import (
    Appointment, AppointmentStatus, Clinic, Patient, Provider,
)
from api.v1.appointments.schemas import (
    AppointmentCreateRequest, AppointmentResponse,
    AppointmentStatusUpdateRequest, AppointmentDetailResponse,
)
from services.appointments import (
    check_conflicts_for_create, check_conflicts_for_reschedule,
    transition_status, reschedule, bulk_delete_by_date,
)
from services.notifications import (
    schedule_cancel_notifications, schedule_reschedule_notifications,
)

router = APIRouter(tags=["appointments"])


# --- ORDER MATTERS ---
# /bulk/date/{date} must be declared before any /{appointment_id} routes.

# 1. GET    /api/appointments                     (was api/main.py:723)
# 2. DELETE /api/appointments/bulk/date/{date}    (was api/main.py:1279)
# 3. GET    /api/appointments/{appointment_id}    (was api/main.py:857)
# 4. POST   /api/appointments                     (was api/main.py:875)
# 5. PUT    /api/appointments/{appointment_id}    (was api/main.py:886)
# 6. DELETE /api/appointments/{appointment_id}    (was api/main.py:920)
# 7. PUT    /api/appointments/{appointment_id}/cancel
# 8. PUT    /api/appointments/{appointment_id}/status
# 9. PUT    /api/appointments/{appointment_id}/reschedule

# For each:
#   - paste the body verbatim
#   - replace direct `@app.<verb>(...)` with `@router.<verb>(...)`
#   - swap inline conflict checks for services.appointments.check_conflicts_for_create
#     / check_conflicts_for_reschedule
#   - swap inline status-transition validation for services.appointments.transition_status
#   - swap inline reschedule orchestration for services.appointments.reschedule
#   - swap inline bulk-delete loop for services.appointments.bulk_delete_by_date
#   - swap inline BackgroundTasks scheduling for services.notifications.*
```

- [ ] **Step 3: Mount in `api/main.py`**

```python
from api.v1.appointments.router import router as _v1_appointments_router
app.include_router(_v1_appointments_router)
```

- [ ] **Step 4: Delete originals from `api/main.py`**

Delete:
- The four appointment Pydantic models (was `api/main.py:83-200`)
- The nine route functions

- [ ] **Step 5: Run the heavy gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py tests/test_busy_block_enforcement.py tests/test_edge_cases.py tests/track_ops -q
```

Expected: green. This is the highest-risk task; pay attention to any test that asserts on:
- 409 `busy_block` shape
- Background-task scheduling
- Appointment status transitions
- Reschedule round-trip behavior

- [ ] **Step 6: Flip `api/serializers.py` lazy import to top-level**

`AppointmentDetailResponse` now lives in `api/v1/appointments/schemas.py`. In `api/serializers.py`:

```python
# Replace this:
def _to_appointment_detail(apt):
    from api.main import AppointmentDetailResponse  # lazy
    ...

# With this:
from api.v1.appointments.schemas import AppointmentDetailResponse

def _to_appointment_detail(apt):
    ...  # body unchanged
```

Run the gate again:

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add api/v1/appointments/ api/main.py api/serializers.py
git commit -m "refactor(api): move v1 appointments routes; wire to services/{appointments,notifications}

Largest single move in the refactor: 9 routes, 4 Pydantic models, multiple
inline orchestration blocks now delegated to services/. Order of route
declarations preserves FastAPI matching: /bulk/date/{date} before /{id}.

Resolves the lazy-import shim in api/serializers.py for AppointmentDetailResponse."
```

---

## Task 11: Move `calendar/` router

**Files:**
- Create: `api/v1/calendar/__init__.py`
- Create: `api/v1/calendar/router.py`
- Modify: `api/main.py`

**Routes moving:**
- `GET  /api/calendar/slots` (line 289)
- `GET  /api/calendar/events` (line 322)
- `POST /api/calendar/events` (line 372)

No new schemas — reuses `AppointmentCreateRequest` / `AppointmentResponse` from `api/v1/appointments/schemas.py` (Task 10).

- [ ] **Step 1: Create `api/v1/calendar/router.py`**

```python
"""v1 calendar router — /api/calendar/slots and /api/calendar/events."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_clinic, get_db
from database.models import Appointment, AppointmentStatus, Clinic, Patient, Provider
from api.v1.appointments.schemas import AppointmentCreateRequest, AppointmentResponse
from services.slots import get_available_slots
from services.appointments import check_conflicts_for_create
from services.notifications import schedule_booking_notifications

router = APIRouter(tags=["calendar"])


# --- paste GET /api/calendar/slots verbatim from api/main.py:289;
#     replace direct tools.slot_utils call with services.slots.get_available_slots. ---

# --- paste GET /api/calendar/events verbatim from api/main.py:322;
#     no service extraction needed (it's a read query). ---

# --- paste POST /api/calendar/events from api/main.py:372 with these swaps:
#       - inline conflict-check → services.appointments.check_conflicts_for_create
#       - inline notification scheduling → services.notifications.schedule_booking_notifications
#     Otherwise byte-identical. ---
```

- [ ] **Step 2: Mount + delete originals from `api/main.py`**

```python
from api.v1.calendar.router import router as _v1_calendar_router
app.include_router(_v1_calendar_router)
```

Delete the three originals.

- [ ] **Step 3: Run gate**

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q -k 'calendar or slot'
uv run pytest tests/test_contract_v1.py tests/test_api.py tests/test_busy_block_enforcement.py -q
```

Expected: green.

- [ ] **Step 4: Commit**

```bash
git add api/v1/calendar/ api/main.py
git commit -m "refactor(api): move v1 calendar routes; wire to services/{slots,appointments,notifications}"
```

---


## Task 12: Move `/health` and `/api/debug/db-info` to `api/system.py`

**Files:**
- Create: `api/system.py`
- Modify: `api/main.py`

**Routes moving:**
- `GET /health` (`api/main.py:1584`)
- `GET /api/debug/db-info` (`api/main.py:1590`)

> These are **not** under `api/v1/` because they aren't part of the v1 contract — they're app-level diagnostics (`/health` is the Cloud Run health check).

- [ ] **Step 1: Create `api/system.py`**

```python
"""App-level system endpoints: health check and debug diagnostics.

Not part of the v1 contract. /health is the Cloud Run health probe.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(tags=["system"])


# --- paste @app.get("/health") body verbatim from api/main.py:1584 ---
# --- paste @app.get("/api/debug/db-info") body verbatim from api/main.py:1590 ---
```

- [ ] **Step 2: Mount + delete + gate + commit**

In `api/main.py`:

```python
from api.system import router as _system_router
app.include_router(_system_router)
```

Delete the two originals.

```bash
uv run pytest tests/test_contract_v1.py tests/test_api.py -q
# Plus a sanity smoke for /health:
uv run python -c "from fastapi.testclient import TestClient; from api.main import app; r = TestClient(app).get('/health'); print(r.status_code, r.json())"
```

Expected: gate green, `/health` returns 200.

```bash
git add api/system.py api/main.py
git commit -m "refactor(api): move /health and /api/debug/db-info to api/system.py"
```

---

## Task 13: Clean up `api/main.py` and verify OpenAPI parity

**Files:**
- Modify: `api/main.py` (remove dead imports, sort, format)

- [ ] **Step 1: Audit `main.py` — what's left**

After Tasks 1-12, `api/main.py` should contain:
- Module docstring
- Stdlib + framework imports
- `database.connection.init_db` import (used by lifespan)
- `lifespan` async context manager
- `app = FastAPI(...)`
- Middleware registration (observability, CORS)
- The re-export block from Task 1: `from api.dependencies import ...`, `from api.serializers import ...`
- The block of `app.include_router(...)` calls — both v1 (new) and v2 (existing)
- Nothing else.

Expected total: ~150 lines.

- [ ] **Step 2: Remove dead imports**

```bash
uv run ruff check api/main.py --select F401
```

Fix any flagged unused imports. Common dead imports after the refactor:
- `joinedload` (was used inside route handlers)
- `Patient`, `Appointment`, etc. ORM models (now only imported in router files)
- `json as _json` (now only in serializers)
- `BackgroundTasks` (now only in router files)

Keep the re-export imports even if `ruff` flags them — they exist deliberately for `from api.main import get_clinic`. Use `# noqa: F401` comments.

- [ ] **Step 3: Snapshot OpenAPI again and diff**

```bash
uv run python -c "import json; from api.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))" > /tmp/openapi-after.json
diff /tmp/openapi-before.json /tmp/openapi-after.json
```

**Acceptable differences:**
- `tags` on operations may have changed (we set `tags=[...]` on each router; the originals likely had none). This is cosmetic — note in the commit message but don't worry about it.

**NOT acceptable:**
- Any change to a `path` string.
- Any added or removed `path`.
- Any change to a `requestBody` schema $ref.
- Any change to a `responses` schema $ref or status code.
- Any change to `parameters` (name, in, required).

If you see unacceptable diffs, the corresponding route did not move byte-identically. Find the affected route, restore the original behavior, re-run the diff.

- [ ] **Step 4: Final full-suite run**

```bash
uv run pytest -q
```

Expected: same passing count as Task 0 Step 2. If `main.py` was a hub for global state any test depended on (it shouldn't be, but verify), failures here surface it.

- [ ] **Step 5: Verify `main.py` line count**

```bash
wc -l api/main.py
```

Expected: roughly 150-200. If it's still over 400, something didn't get moved — read it through and finish the job.

- [ ] **Step 6: Commit**

```bash
git add api/main.py
git commit -m "refactor(api): clean up main.py after v1 router split

main.py is now app construction + middleware + include_router calls only.
Re-exports of get_clinic, get_clinic_id, _busy_block_envelope, and
_to_appointment_detail are kept so v2 routers and tests that import from
api.main continue to work.

OpenAPI diff vs pre-refactor: paths/schemas/parameters identical; only
operation tags changed (cosmetic).
"
```

---

## Done check

After Task 13:

- [ ] `api/main.py` is ~150-200 lines.
- [ ] `api/v1/{calendar,appointments,patients,providers,catalog,leads,clinics}/` each have a `router.py` (and `schemas.py` where applicable).
- [ ] `api/dependencies.py`, `api/serializers.py`, `api/system.py` exist.
- [ ] `services/{__init__.py,appointments.py,notifications.py,slots.py}` exist; the empty leftover dir is now a real package.
- [ ] `from api.main import get_clinic` still works (14 v2 routers + tests rely on it).
- [ ] `uv run pytest -q` matches the baseline pass count from Task 0 Step 2.
- [ ] OpenAPI diff shows only `tags` differences, no path/schema differences.
- [ ] Every task above produced a self-contained commit.

## Out of scope (do not start in this branch)

- Extracting the `frontend/` Next.js app to its own repo (separate follow-up spec).
- Deleting the empty `api/routes/` directory (do it in a tiny cleanup PR after this lands).
- Renaming any v1 URL or response field.
- Touching `api/v2/`.
- Migrating `dental-agent` off v1.

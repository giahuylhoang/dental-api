"""Portal admin router — Firebase-authenticated /api/portal/* layer."""

from fastapi import APIRouter, Depends

from api.portal.deps import require_clinic_access
from api.portal import whoami, routing, greeting, calls, schedule, dashboard, patients


router = APIRouter(prefix="/api/portal")
router.include_router(whoami.router, prefix="/whoami", tags=["portal:whoami"])

clinic_scoped = APIRouter(
    prefix="/clinics/{clinic_id}",
    dependencies=[Depends(require_clinic_access)],
)

# Sub-routers (routing, patients, calls, greeting, dashboard, schedule) added in later tasks.
clinic_scoped.include_router(routing.router, prefix="/routing", tags=["portal:routing"])
clinic_scoped.include_router(greeting.router, prefix="/greeting", tags=["portal:greeting"])
clinic_scoped.include_router(calls.router, prefix="/calls", tags=["portal:calls"])
clinic_scoped.include_router(schedule.router, prefix="/schedule", tags=["portal:schedule"])
clinic_scoped.include_router(dashboard.router, prefix="/dashboard", tags=["portal:dashboard"])
clinic_scoped.include_router(patients.router, prefix="/patients", tags=["portal:patients"])

router.include_router(clinic_scoped)

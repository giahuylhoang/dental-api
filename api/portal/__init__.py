"""Portal admin router — Firebase-authenticated /api/portal/* layer."""

from fastapi import APIRouter, Depends

from api.portal.deps import PortalUser, get_portal_user, require_clinic_access
from api.portal import whoami, routing, greeting, calls, schedule


def _clinic_access(clinic_id: str, user: PortalUser = Depends(get_portal_user)) -> str:
    return require_clinic_access(clinic_id, user)


router = APIRouter(prefix="/api/portal")
router.include_router(whoami.router, prefix="/whoami", tags=["portal:whoami"])

clinic_scoped = APIRouter(
    prefix="/clinics/{clinic_id}",
    dependencies=[Depends(_clinic_access)],
)

# Sub-routers (routing, patients, calls, greeting, dashboard, schedule) added in later tasks.
clinic_scoped.include_router(routing.router, prefix="/routing", tags=["portal:routing"])
clinic_scoped.include_router(greeting.router, prefix="/greeting", tags=["portal:greeting"])
clinic_scoped.include_router(calls.router, prefix="/calls", tags=["portal:calls"])
clinic_scoped.include_router(schedule.router, prefix="/schedule", tags=["portal:schedule"])

router.include_router(clinic_scoped)

"""GET /api/portal/whoami — echo decoded user."""

from fastapi import APIRouter, Depends

from api.portal.deps import PortalUser, get_portal_user

router = APIRouter()


@router.get("", response_model=PortalUser)
def whoami(user: PortalUser = Depends(get_portal_user)) -> PortalUser:
    return user

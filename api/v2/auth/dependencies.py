"""FastAPI auth dependencies: JWT parsing, permission checks, audit context."""
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.connection import get_db
from database.auth.models import User
from database.auth.audit import set_audit_context

_bearer = HTTPBearer(auto_error=False)

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 14
ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        # Per-process random default for dev; tests pin via monkeypatch
        if not hasattr(get_jwt_secret, "_dev_secret"):
            get_jwt_secret._dev_secret = os.urandom(32).hex()
        return get_jwt_secret._dev_secret
    return secret


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    if user.locked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked")
    return user


def require_permissions(*perms: str):
    """Dependency factory: raises 403 if current user lacks any of the required permissions."""
    def _dep(user: User = Depends(get_current_user)) -> User:
        user_perms = _collect_permissions(user)
        if "*.*" in user_perms:
            return user
        for perm in perms:
            if perm not in user_perms:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Missing permission: {perm}")
        return user
    return _dep


def _collect_permissions(user: User) -> set:
    perms = set()
    for ur in user.user_roles:
        for p in (ur.role.permissions or []):
            perms.add(p)
    return perms


def audit_context(request: Request, user: User = Depends(get_current_user)) -> None:
    """Populate audit context var for the duration of the request."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    set_audit_context(user.id, ip, ua)

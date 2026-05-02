"""Auth endpoints: login, refresh, logout, me."""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.auth.models import User, RefreshToken, UserRole
from database.models import DEFAULT_CLINIC_ID
from api.v2.auth.dependencies import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ALGORITHM,
    get_jwt_secret,
    get_current_user,
)

router = APIRouter(prefix="/api/v2/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode(), hashed.encode())

MAX_FAILED_LOGINS = 5


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_access_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": exp}, get_jwt_secret(), algorithm=ALGORITHM)


def _make_refresh_token_str(user_id: str) -> str:
    import secrets
    return secrets.token_urlsafe(48)


def _get_clinic_id(request: Request) -> str:
    return request.headers.get("X-Clinic-Id", DEFAULT_CLINIC_ID).strip() or DEFAULT_CLINIC_ID


# ── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    perms: set = set()
    roles = []
    for ur in user.user_roles:
        roles.append(ur.role.name)
        for p in (ur.role.permissions or []):
            perms.add(p)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": roles,
        "permissions": list(perms),
    }


def _issue_tokens(user: User, db: Session):
    access = _make_access_token(user.id)
    raw_refresh = _make_refresh_token_str(user.id)
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_refresh),
        expires_at=expires,
    )
    db.add(rt)
    db.commit()
    return access, raw_refresh, ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    clinic_id = _get_clinic_id(request)
    user = db.query(User).filter(User.clinic_id == clinic_id, User.email == body.email).first()

    def _bad_creds():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user is None:
        _bad_creds()

    if user.locked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked")

    if not _verify_password(body.password, user.password_hash):
        count = int(user.failed_login_count or "0") + 1
        user.failed_login_count = str(count)
        if count >= MAX_FAILED_LOGINS:
            user.locked_at = datetime.utcnow()
        db.commit()
        _bad_creds()

    # Successful login
    user.failed_login_count = "0"
    user.last_login_at = datetime.utcnow()
    db.commit()

    access, raw_refresh, expires_in = _issue_tokens(user, db)
    return {
        "access_token": access,
        "refresh_token": raw_refresh,
        "expires_in": expires_in,
        "user": _user_dict(user),
    }


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(body.refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt is None or rt.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = db.query(User).filter(User.id == rt.user_id).first()
    if user is None or not user.is_active or user.locked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

    # Revoke old token
    rt.revoked_at = datetime.utcnow()
    db.commit()

    access, raw_refresh, expires_in = _issue_tokens(user, db)
    return {"access_token": access, "refresh_token": raw_refresh, "expires_in": expires_in}


@router.post("/logout")
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(body.refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_dict(user)

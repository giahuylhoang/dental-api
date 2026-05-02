"""Admin endpoints: users, roles, audit-log."""
from datetime import datetime
from typing import Optional, List

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.auth.models import User, Role, UserRole, AuditLog
from database.models import DEFAULT_CLINIC_ID
from api.v2.auth.dependencies import get_current_user, require_permissions

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _clinic_id(request: Request) -> str:
    return request.headers.get("X-Clinic-Id", DEFAULT_CLINIC_ID).strip() or DEFAULT_CLINIC_ID


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class RoleAssign(BaseModel):
    role_id: str


class RoleCreate(BaseModel):
    name: str
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None


# ── User endpoints ────────────────────────────────────────────────────────────

@router.post("/users", dependencies=[Depends(require_permissions("users.write"))])
def create_user(body: UserCreate, request: Request, db: Session = Depends(get_db)):
    clinic_id = _clinic_id(request)
    existing = db.query(User).filter(User.clinic_id == clinic_id, User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered in this clinic")
    user = User(
        clinic_id=clinic_id,
        email=body.email,
        password_hash=_hash_password(body.password),
        full_name=body.full_name,
        is_active=body.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.get("/users", dependencies=[Depends(require_permissions("users.read"))])
def list_users(
    request: Request,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    clinic_id = _clinic_id(request)
    users = db.query(User).filter(User.clinic_id == clinic_id).offset(offset).limit(limit).all()
    return [_user_out(u) for u in users]


@router.put("/users/{user_id}", dependencies=[Depends(require_permissions("users.write"))])
def update_user(user_id: str, body: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password is not None:
        user.password_hash = _hash_password(body.password)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post("/users/{user_id}/roles", dependencies=[Depends(require_permissions("users.write"))])
def assign_role(user_id: str, body: RoleAssign, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.query(Role).filter(Role.id == body.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    existing = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == body.role_id).first()
    if not existing:
        db.add(UserRole(user_id=user_id, role_id=body.role_id))
        db.commit()
    return {"ok": True}


# ── Role endpoints ────────────────────────────────────────────────────────────

@router.get("/roles", dependencies=[Depends(require_permissions("users.read"))])
def list_roles(request: Request, db: Session = Depends(get_db)):
    clinic_id = _clinic_id(request)
    roles = db.query(Role).filter(
        (Role.clinic_id == clinic_id) | (Role.clinic_id == None)  # noqa: E711
    ).all()
    return [_role_out(r) for r in roles]


@router.post("/roles", dependencies=[Depends(require_permissions("users.write"))])
def create_role(body: RoleCreate, request: Request, db: Session = Depends(get_db)):
    clinic_id = _clinic_id(request)
    role = Role(clinic_id=clinic_id, name=body.name, permissions=body.permissions)
    db.add(role)
    db.commit()
    db.refresh(role)
    return _role_out(role)


@router.put("/roles/{role_id}", dependencies=[Depends(require_permissions("users.write"))])
def update_role(role_id: str, body: RoleUpdate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if body.name is not None:
        role.name = body.name
    if body.permissions is not None:
        role.permissions = body.permissions
    db.commit()
    db.refresh(role)
    return _role_out(role)


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", dependencies=[Depends(require_permissions("audit.read"))])
def get_audit_log(
    request: Request,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    clinic_id = _clinic_id(request)
    q = db.query(AuditLog).filter(AuditLog.clinic_id == clinic_id)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    logs = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [_audit_out(l) for l in logs]


# ── Serializers ───────────────────────────────────────────────────────────────

def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "clinic_id": user.clinic_id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "locked_at": user.locked_at.isoformat() if user.locked_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _role_out(role: Role) -> dict:
    return {
        "id": role.id,
        "clinic_id": role.clinic_id,
        "name": role.name,
        "permissions": role.permissions or [],
    }


def _audit_out(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "clinic_id": log.clinic_id,
        "user_id": log.user_id,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "before": log.before,
        "after": log.after,
        "ip": log.ip,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }

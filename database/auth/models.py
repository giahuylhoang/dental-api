"""Auth/RBAC/Audit ORM models."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, JSON, PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    locked_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    failed_login_count = Column(String, default="0", nullable=False)  # stored as str for SQLite compat
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("clinic_id", "email", name="uq_user_clinic_email"),)

    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=True)  # null = system role
    name = Column(String, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id"),)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=_uuid)
    clinic_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)       # insert / update / delete
    entity_type = Column(String, nullable=False)  # table name
    entity_id = Column(String, nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

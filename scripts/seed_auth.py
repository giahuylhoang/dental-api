"""
Seed default roles and an admin user for the 'default' clinic.

WARNING: DO NOT run in production. For dev/test only.
Default admin credentials: admin@example.com / changeme

Usage:
    DATABASE_URL=sqlite:///./dental_clinic.db python scripts/seed_auth.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.connection import SessionLocal, Base, engine
import database.auth  # noqa: F401 — register auth models
import database.models  # noqa: F401

from database.auth.models import User, Role, UserRole
from database.models import DEFAULT_CLINIC_ID
import bcrypt as _bcrypt


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

ROLES = {
    "admin": ["*.*"],
    "denturist": [
        "patients.*", "appointments.*", "clinical.*", "lab.*", "treatment_plans.*",
    ],
    "assistant": [
        "patients.read", "patients.write", "appointments.*", "clinical.read", "lab.*",
    ],
    "front_desk": [
        "patients.read", "patients.write", "appointments.*",
        "leads.*", "communications.*", "billing.read",
    ],
    "accountant": [
        "billing.*", "insurance.*", "patients.read", "appointments.read",
    ],
}

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "changeme"


def seed(clinic_id: str = DEFAULT_CLINIC_ID) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        role_map = {}
        for name, perms in ROLES.items():
            role = db.query(Role).filter(Role.name == name, Role.clinic_id == None).first()  # noqa: E711
            if role is None:
                role = Role(name=name, clinic_id=None, permissions=perms)
                db.add(role)
                db.flush()
            else:
                role.permissions = perms
            role_map[name] = role

        admin_user = db.query(User).filter(User.clinic_id == clinic_id, User.email == ADMIN_EMAIL).first()
        if admin_user is None:
            admin_user = User(
                clinic_id=clinic_id,
                email=ADMIN_EMAIL,
                password_hash=_hash_password(ADMIN_PASSWORD),
                full_name="Admin",
                is_active=True,
            )
            db.add(admin_user)
            db.flush()

        admin_role = role_map["admin"]
        existing_ur = db.query(UserRole).filter(
            UserRole.user_id == admin_user.id, UserRole.role_id == admin_role.id
        ).first()
        if existing_ur is None:
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

        db.commit()
        print(f"Seeded roles and admin user ({ADMIN_EMAIL}) for clinic '{clinic_id}'.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

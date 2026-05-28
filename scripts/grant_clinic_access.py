"""Grant / revoke / list a user's clinic memberships.

Usage:
    python scripts/grant_clinic_access.py \\
        --email alice@example.com \\
        --password 'OneTimePassword!' \\
        --clinics market-mall-denture,northeast-denture-clinic

    python scripts/grant_clinic_access.py --revoke \\
        --email alice@example.com \\
        --clinics market-mall-denture

    python scripts/grant_clinic_access.py --list --email alice@example.com

Engineer-only operation. Idempotent: re-running grant with the same args
does not produce duplicate rows.
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

from sqlalchemy.orm import Session

from database.auth import UserClinicMembership
from database.connection import SessionLocal
from database.models import Clinic


logger = logging.getLogger(__name__)


class UnknownClinicError(Exception):
    """Raised when a clinic_id argument does not exist in the DB."""


def _ensure_firebase_user(email: str, password: str):
    """Create the Firebase user, or fetch the existing record. Returns the Firebase UserRecord."""
    import firebase_admin
    from firebase_admin import auth as firebase_auth

    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    try:
        user = firebase_auth.get_user_by_email(email)
        logger.info("Firebase user already exists: uid=%s email=%s", user.uid, email)
        return user
    except firebase_auth.UserNotFoundError:
        user = firebase_auth.create_user(email=email, password=password)
        logger.info("Created Firebase user: uid=%s email=%s", user.uid, email)
        return user


def grant(
    db: Session,
    email: str,
    password: str,
    clinic_ids: Iterable[str],
) -> dict:
    clinic_ids = list(clinic_ids)
    existing = {c.id for c in db.query(Clinic).filter(Clinic.id.in_(clinic_ids)).all()}
    unknown = set(clinic_ids) - existing
    if unknown:
        raise UnknownClinicError(f"unknown clinic ids: {sorted(unknown)}")

    user = _ensure_firebase_user(email=email, password=password)
    uid = user.uid

    inserted = []
    for cid in clinic_ids:
        already = (
            db.query(UserClinicMembership)
            .filter_by(uid=uid, clinic_id=cid)
            .first()
        )
        if already:
            continue
        db.add(UserClinicMembership(uid=uid, clinic_id=cid, email=email))
        inserted.append(cid)
    db.commit()
    return {"uid": uid, "email": email, "granted": inserted, "requested": clinic_ids}


def revoke(db: Session, uid: str, clinic_ids: Iterable[str]) -> int:
    deleted = (
        db.query(UserClinicMembership)
        .filter(
            UserClinicMembership.uid == uid,
            UserClinicMembership.clinic_id.in_(list(clinic_ids)),
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def list_memberships(db: Session, uid: str) -> list[str]:
    return [
        m.clinic_id
        for m in db.query(UserClinicMembership)
        .filter(UserClinicMembership.uid == uid)
        .order_by(UserClinicMembership.clinic_id)
        .all()
    ]


def _resolve_uid_from_email(db: Session, email: str) -> str | None:
    row = (
        db.query(UserClinicMembership)
        .filter(UserClinicMembership.email == email)
        .first()
    )
    return row.uid if row else None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--email", required=True)
    p.add_argument("--password", default=None, help="Required for first-time grant.")
    p.add_argument("--clinics", default="", help="Comma-separated clinic_ids.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--revoke", action="store_true")
    mode.add_argument("--list", action="store_true")
    args = p.parse_args(argv)

    db = SessionLocal()
    try:
        if args.list:
            uid = _resolve_uid_from_email(db, args.email)
            if uid is None:
                print(f"No memberships found for {args.email}")
                return 0
            print(f"{args.email} (uid={uid})")
            for cid in list_memberships(db, uid):
                print(f"  - {cid}")
            return 0

        clinics = [c.strip() for c in args.clinics.split(",") if c.strip()]
        if not clinics:
            print("--clinics is required for grant/revoke", file=sys.stderr)
            return 2

        if args.revoke:
            uid = _resolve_uid_from_email(db, args.email)
            if uid is None:
                print(f"No memberships found for {args.email}; nothing to revoke.")
                return 0
            n = revoke(db, uid=uid, clinic_ids=clinics)
            print(f"Revoked {n} memberships for uid={uid}")
            return 0

        if not args.password:
            print("--password is required for grant", file=sys.stderr)
            return 2
        result = grant(db, email=args.email, password=args.password, clinic_ids=clinics)
        print(
            f"Granted access for {args.email} (uid={result['uid']}): "
            f"newly added {result['granted']}, total requested {result['requested']}"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(main())

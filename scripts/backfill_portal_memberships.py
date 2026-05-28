"""One-shot: backfill user_clinic_memberships from Firebase custom claims.

Run from a workstation with prod-DB access AFTER deploying the CRM auth
plan migration. Idempotent — re-running adds nothing if rows already
exist.

Usage:
    DATABASE_URL=postgresql://... \\
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json \\
    python scripts/backfill_portal_memberships.py
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from sqlalchemy.orm import Session

# Lazy-import firebase so the test suite can monkeypatch it without
# requiring a real Firebase project.
try:
    from firebase_admin import auth as fb_auth
    list_users = fb_auth.list_users
except ImportError:                                 # pragma: no cover
    list_users = None  # type: ignore[assignment]

from database.auth.memberships import UserClinicMembership
from database.connection import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("backfill_portal_memberships")


def run_backfill(db: Session) -> Dict[str, int]:
    """Iterate all Firebase users, write a membership row per clinic_ids claim.

    Returns a summary dict: users_scanned, rows_inserted, rows_skipped_existing,
    users_without_claim.
    """
    if list_users is None:                          # pragma: no cover
        raise RuntimeError("firebase-admin not installed")

    summary = {
        "users_scanned": 0,
        "rows_inserted": 0,
        "rows_skipped_existing": 0,
        "users_without_claim": 0,
    }

    page = list_users()
    for user in page.iterate_all():
        summary["users_scanned"] += 1
        claims: Any = user.custom_claims or {}
        clinic_ids = list(claims.get("clinic_ids") or [])
        if not clinic_ids:
            summary["users_without_claim"] += 1
            continue
        for cid in clinic_ids:
            exists = (
                db.query(UserClinicMembership)
                .filter_by(uid=user.uid, clinic_id=cid)
                .first()
            )
            if exists:
                summary["rows_skipped_existing"] += 1
                continue
            db.add(UserClinicMembership(
                uid=user.uid,
                clinic_id=cid,
                email=user.email or "",
            ))
            summary["rows_inserted"] += 1
    db.commit()
    return summary


def main() -> int:
    db = SessionLocal()
    try:
        summary = run_backfill(db)
    finally:
        db.close()
    _log.info("backfill complete: %s", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())

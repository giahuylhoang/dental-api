#!/usr/bin/env python3
"""
Migration: Add address, contact_phone, booking_notification_email to clinics.

Run: DATABASE_URL=sqlite:///./dental_clinic.db python scripts/migrate_clinic_contact_fields.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from database.connection import engine
from database.models import Base
from sqlalchemy import text


def column_exists(conn, table: str, column: str, is_sqlite: bool) -> bool:
    if is_sqlite:
        r = conn.execute(text(f"PRAGMA table_info({table})"))
        for row in r:
            if row[1] == column:
                return True
        return False
    r = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return r.fetchone() is not None


def run_migration():
    is_sqlite = "sqlite" in str(engine.url)
    Base.metadata.tables["clinics"].create(engine, checkfirst=True)

    columns = [
        ("address", "TEXT" if is_sqlite else "TEXT"),
        ("contact_phone", "VARCHAR" if is_sqlite else "VARCHAR(255)"),
        ("booking_notification_email", "VARCHAR" if is_sqlite else "VARCHAR(255)"),
    ]

    with engine.connect() as conn:
        for col_name, col_type in columns:
            if column_exists(conn, "clinics", col_name, is_sqlite):
                print(f"  Column clinics.{col_name} already exists, skip")
                continue
            conn.execute(text(f"ALTER TABLE clinics ADD COLUMN {col_name} {col_type}"))
            conn.commit()
            print(f"  Added clinics.{col_name}")

    print("Migration complete.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Migration: Add multi-tenant clinic_id to all tenant tables.

Creates clinics table, adds clinic_id column to patients, doctors, services,
appointments, leads. Inserts default clinic and backfills existing rows.

Run: DATABASE_URL=sqlite:///./dental_clinic.db python scripts/migrate_add_clinics.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from database.connection import engine
from database.models import Base, Clinic, DEFAULT_CLINIC_ID
from sqlalchemy import text


def column_exists(conn, table: str, column: str, is_sqlite: bool) -> bool:
    """Check if column exists in table."""
    if is_sqlite:
        r = conn.execute(text(f"PRAGMA table_info({table})"))
        for row in r:
            if row[1] == column:
                return True
        return False
    else:
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
    with engine.connect() as conn:
        # 1. Create clinics table
        Base.metadata.tables["clinics"].create(engine, checkfirst=True)
        conn.commit()

        # 2. Add clinic_id to tenant tables if missing
        tenant_tables = ["patients", "doctors", "services", "appointments", "leads"]
        for table in tenant_tables:
            if not column_exists(conn, table, "clinic_id", is_sqlite):
                # SQLite: DEFAULT cannot use bound params in ALTER TABLE
                default_val = f"'{DEFAULT_CLINIC_ID}'"
                if is_sqlite:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN clinic_id VARCHAR DEFAULT {default_val}")
                    )
                else:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} ADD COLUMN clinic_id VARCHAR NOT NULL DEFAULT :d"
                        ),
                        {"d": DEFAULT_CLINIC_ID},
                    )
                conn.commit()
                print(f"  Added clinic_id to {table}")

        # 3. Insert default clinic
        params = {"id": DEFAULT_CLINIC_ID, "name": "Default Clinic", "tz": "America/Edmonton", "start": 9, "end": 17}
        if is_sqlite:
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO clinics (id, name, timezone, working_hour_start, working_hour_end) "
                    "VALUES (:id, :name, :tz, :start, :end)"
                ),
                params,
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO clinics (id, name, timezone, working_hour_start, working_hour_end) "
                    "VALUES (:id, :name, :tz, :start, :end) ON CONFLICT (id) DO NOTHING"
                ),
                params,
            )
        conn.commit()

        # 4. Backfill null clinic_id (for PostgreSQL where we might have added nullable first)
        if not is_sqlite:
            for table in tenant_tables:
                conn.execute(
                    text(f"UPDATE {table} SET clinic_id = :d WHERE clinic_id IS NULL"),
                    {"d": DEFAULT_CLINIC_ID},
                )
            conn.commit()

    print("Migration complete.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

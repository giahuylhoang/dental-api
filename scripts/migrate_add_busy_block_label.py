#!/usr/bin/env python3
"""
Migration: Add `label` column to provider_busy_blocks.

Run: DATABASE_URL=sqlite:///./dental_clinic.db python scripts/migrate_add_busy_block_label.py
     DATABASE_URL=postgresql://... python scripts/migrate_add_busy_block_label.py
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
    Base.metadata.tables["provider_busy_blocks"].create(engine, checkfirst=True)

    col_type = "VARCHAR" if is_sqlite else "VARCHAR(64)"
    with engine.connect() as conn:
        if column_exists(conn, "provider_busy_blocks", "label", is_sqlite):
            print("  Column provider_busy_blocks.label already exists, skip")
        else:
            conn.execute(text(f"ALTER TABLE provider_busy_blocks ADD COLUMN label {col_type}"))
            conn.commit()
            print("  Added provider_busy_blocks.label")

    print("Migration complete.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

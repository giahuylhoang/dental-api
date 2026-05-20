#!/usr/bin/env python3
"""
Migration: Busy blocks v2 schema.

Adds three nullable columns to `provider_busy_blocks` to support multi-weekday
recurrence, specific-date one-offs, and bounded recurrence end dates:

  - weekdays         VARCHAR    JSON-encoded list of ints, e.g. "[0,2,4]"
  - specific_date    DATE       Calendar date for a one-off block
  - recurrence_until DATE       Inclusive end date for weekday recurrence

Also relaxes the legacy `weekday` column to nullable on Postgres (SQLite ALTERs
don't support DROP NOT NULL; if you hit a constraint there, recreate the DB).

After adding the columns, backfills `weekdays = [weekday]` for any row that
still uses the legacy single-day field, so existing rules keep working under
the new code path.

Run:
  DATABASE_URL=sqlite:///./dental_clinic.db python scripts/migrate_busy_block_v2.py
  DATABASE_URL=postgresql://... python scripts/migrate_busy_block_v2.py
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
    # Make sure the table exists (fresh DBs).
    Base.metadata.tables["provider_busy_blocks"].create(engine, checkfirst=True)

    str_type = "VARCHAR"
    date_type = "DATE"
    with engine.connect() as conn:
        new_columns = [
            ("weekdays", str_type),
            ("specific_date", date_type),
            ("recurrence_until", date_type),
        ]
        for col, typ in new_columns:
            if column_exists(conn, "provider_busy_blocks", col, is_sqlite):
                print(f"  Column provider_busy_blocks.{col} already exists, skip")
            else:
                conn.execute(text(
                    f"ALTER TABLE provider_busy_blocks ADD COLUMN {col} {typ}"
                ))
                conn.commit()
                print(f"  Added provider_busy_blocks.{col}")

        # Backfill: every row that has a legacy `weekday` but no `weekdays`
        # gets `weekdays = '[' || weekday || ']'`. The string-cat form works on
        # both SQLite and Postgres.
        if column_exists(conn, "provider_busy_blocks", "weekday", is_sqlite):
            result = conn.execute(text(
                "UPDATE provider_busy_blocks "
                "SET weekdays = '[' || weekday || ']' "
                "WHERE weekdays IS NULL AND weekday IS NOT NULL"
            ))
            conn.commit()
            print(f"  Backfilled weekdays for {result.rowcount} row(s).")

        # Relax legacy weekday NOT NULL so new rows can omit it.
        if not is_sqlite:
            try:
                conn.execute(text(
                    "ALTER TABLE provider_busy_blocks "
                    "ALTER COLUMN weekday DROP NOT NULL"
                ))
                conn.commit()
                print("  Relaxed provider_busy_blocks.weekday NOT NULL")
            except Exception as e:
                print(f"  (weekday DROP NOT NULL skipped: {e})")
        else:
            # SQLite can't ALTER COLUMN — rebuild the table when `weekday` is
            # still declared NOT NULL on disk.
            schema = conn.execute(text(
                "SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name='provider_busy_blocks'"
            )).scalar() or ""
            if "weekday INTEGER NOT NULL" in schema:
                print("  Rebuilding provider_busy_blocks to drop weekday NOT NULL …")
                conn.execute(text("PRAGMA foreign_keys = OFF"))
                conn.execute(text("""
                    CREATE TABLE provider_busy_blocks__new (
                        id INTEGER NOT NULL,
                        clinic_id VARCHAR NOT NULL,
                        provider_id INTEGER NOT NULL,
                        weekday INTEGER,
                        weekdays VARCHAR,
                        specific_date DATE,
                        recurrence_until DATE,
                        start_hour INTEGER NOT NULL,
                        start_minute INTEGER NOT NULL,
                        end_hour INTEGER NOT NULL,
                        end_minute INTEGER NOT NULL,
                        label VARCHAR,
                        PRIMARY KEY (id),
                        FOREIGN KEY(clinic_id) REFERENCES clinics (id),
                        FOREIGN KEY(provider_id) REFERENCES providers (id)
                    )
                """))
                conn.execute(text("""
                    INSERT INTO provider_busy_blocks__new
                        (id, clinic_id, provider_id, weekday, weekdays,
                         specific_date, recurrence_until,
                         start_hour, start_minute, end_hour, end_minute, label)
                    SELECT id, clinic_id, provider_id, weekday, weekdays,
                           specific_date, recurrence_until,
                           start_hour, start_minute, end_hour, end_minute, label
                    FROM provider_busy_blocks
                """))
                conn.execute(text("DROP TABLE provider_busy_blocks"))
                conn.execute(text(
                    "ALTER TABLE provider_busy_blocks__new RENAME TO provider_busy_blocks"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_provider_busy_blocks_provider_weekday "
                    "ON provider_busy_blocks (provider_id, weekday)"
                ))
                conn.execute(text("PRAGMA foreign_keys = ON"))
                conn.commit()
                print("  Rebuilt provider_busy_blocks (weekday now nullable).")

    print("Migration complete.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

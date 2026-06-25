"""Database connection and session management."""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from .env files
# Try multiple locations: project root, current directory
project_root = Path(__file__).parent.parent
env_files = [
    project_root / ".env.local",
    project_root / ".env",
    Path.cwd() / ".env.local",
    Path.cwd() / ".env",
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        break

# Get database URL from environment
# Priority: Vercel Postgres variables → DATABASE_URL → SQLite default
# Vercel Postgres automatically provides POSTGRES_URL and POSTGRES_PRISMA_URL
DATABASE_URL = (
    os.getenv("POSTGRES_URL") or             # Vercel Postgres direct connection
    os.getenv("POSTGRES_PRISMA_URL") or      # Vercel Postgres Prisma connection
    os.getenv("POSTGRES_URL_NON_POOLING") or # Vercel Postgres non-pooling
    os.getenv("DATABASE_URL") or             # Custom DATABASE_URL (for Supabase, etc.)
    "sqlite:////tmp/dental_clinic.db"        # Fallback to SQLite for local dev (writable)
)

# Normalize postgres:// to postgresql:// (SQLAlchemy requires postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Remove Supabase-specific parameters that SQLAlchemy doesn't understand
# Supabase adds parameters like "supa=base-pooler.x" which cause errors
if "supa=" in DATABASE_URL:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(DATABASE_URL)
    query_params = parse_qs(parsed.query)
    # Remove Supabase-specific parameters
    query_params.pop("supa", None)
    # Rebuild URL without Supabase params
    new_query = urlencode(query_params, doseq=True)
    DATABASE_URL = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

# Create engine.
#
# Pool tuning for Postgres in prod: cap connections so a Cloud Run rollover
# (two revisions running side-by-side during traffic shift) can't exhaust
# the database's max_connections. With pool_size=5, max_overflow=10, each
# Cloud Run instance holds at most 15 connections, so even two instances
# during a roll stay under 30 — well under our 100-slot ceiling.
# pool_pre_ping detects connections that died while idle (Cloud SQL idle
# timeout); pool_recycle proactively closes connections >30 min old so
# they never reach the server-side timeout. Both keep "stale connection"
# OperationalErrors out of request handlers.
#
# pool_timeout=10: fail fast on pool exhaustion. The 2026-06-19 incident
# (CRM "keeps loading") was a QueuePool-exhaustion hang — the background
# reminder scheduler held a session across a blocking Twilio send, all 15
# connections stalled, and checkouts queued on the 30s SQLAlchemy default
# until requests hit the ~120s Cloud Run request timeout and 500'd, so the
# spinner never resolved. A 10s checkout timeout surfaces the failure well
# under the request timeout instead of hanging. Do NOT switch to NullPool
# (it would worsen cold-start latency). See 2026-06-25 plan.
def build_engine_kwargs(database_url: str) -> dict:
    """Return the create_engine kwargs for a given DATABASE_URL.

    Extracted (and unit-guarded by tests/test_db_connection_pool.py) so the
    Postgres pool_timeout=10 setting can't be silently regressed by a future
    edit. SQLite (tests/local) gets only check_same_thread=False.
    """
    kwargs: dict = {}
    if "sqlite" in database_url:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=10,
            pool_recycle=1800,
        )
    return kwargs


_is_sqlite = "sqlite" in DATABASE_URL
_engine_kwargs = build_engine_kwargs(DATABASE_URL)
engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Register SQL observability events (off by default, enable with OBSERVE_SQL=1)
from database.observability import register_sql_events
register_sql_events(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency function to get database session.
    Use with FastAPI's Depends() for dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    from database.models import Patient, Appointment, Provider, Service, Clinic, Lead
    Base.metadata.create_all(bind=engine)

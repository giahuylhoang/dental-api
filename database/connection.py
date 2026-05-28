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
_is_sqlite = "sqlite" in DATABASE_URL
_engine_kwargs: dict = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )
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

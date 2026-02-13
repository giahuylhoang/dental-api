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
    os.getenv("POSTGRES_URL") or           # Vercel Postgres direct connection
    os.getenv("POSTGRES_PRISMA_URL") or    # Vercel Postgres Prisma connection
    os.getenv("POSTGRES_URL_NON_POOLING") or # Vercel Postgres non-pooling
    os.getenv("DATABASE_URL") or            # Custom DATABASE_URL (for Supabase, etc.)
    "sqlite:///./dental_clinic.db"          # Fallback to SQLite for local dev
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

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

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
    from database.models import Patient, Appointment, Doctor, Service
    Base.metadata.create_all(bind=engine)

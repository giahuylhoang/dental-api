"""App-level system endpoints: health check and debug diagnostics.

Not part of the v1 contract. /health is the Cloud Run health probe.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Provider

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/api/debug/db-info")
async def debug_db_info(db: Session = Depends(get_db)):
    """
    Debug: which database we're connected to and provider count.
    Use this to verify Railway is hitting the same Supabase as the dashboard.
    """
    from database.connection import engine
    url = engine.url
    # Safe to expose: host and db name only (no password)
    db_host = url.host if hasattr(url, "host") else ("sqlite" if "sqlite" in str(url) else "unknown")
    db_name = url.database if hasattr(url, "database") else None
    provider_count = db.query(Provider).count()
    return {
        "database_host": db_host,
        "database_name": db_name,
        "provider_count": provider_count,
    }

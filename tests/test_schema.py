"""
Schema and init_db tests for pre-deployment validation.

Validates DB schema (all tables, relationships) and seed logic.
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import (
    Clinic,
    Provider,
    ProviderBusyBlock,
    Service,
    DEFAULT_CLINIC_ID,
)
import database.models  # noqa: F401 - ensure all models registered

# Import seed function from init_database (uses our test session)
from scripts.init_database import seed_market_mall_denture, MARKET_MALL_CLINIC_ID

SQLITE_TEST_URL = "sqlite:///:memory:"

EXPECTED_TABLES = [
    "clinics",
    "patients",
    "providers",
    "provider_busy_blocks",
    "provider_availability",
    "services",
    "appointments",
    "leads",
]


def test_database_schema_tables_exist():
    """After create_all, all expected tables exist."""
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for expected in EXPECTED_TABLES:
        assert expected in tables, f"Missing table: {expected}"
    engine.dispose()


def test_seed_market_mall_denture_creates_expected_data(db_session):
    """seed_market_mall_denture creates clinic, providers 101/102, service 700, busy blocks."""
    # Ensure default clinic exists (seed_initial_data normally does this first)
    if db_session.query(Clinic).filter(Clinic.id == DEFAULT_CLINIC_ID).first() is None:
        db_session.add(
            Clinic(
                id=DEFAULT_CLINIC_ID,
                name="Default Clinic",
                timezone="America/Edmonton",
                working_hour_start=9,
                working_hour_end=17,
            )
        )
        db_session.commit()

    seed_market_mall_denture(db_session)
    db_session.commit()

    clinic = db_session.query(Clinic).filter(Clinic.id == MARKET_MALL_CLINIC_ID).first()
    assert clinic is not None
    assert clinic.name == "Market Mall Denture"
    assert clinic.address and "40th Ave NW" in clinic.address
    assert clinic.contact_phone == "(403) 247-6222"

    providers = db_session.query(Provider).filter(
        Provider.clinic_id == MARKET_MALL_CLINIC_ID
    ).all()
    assert len(providers) == 2
    ids = {p.id for p in providers}
    assert 101 in ids
    assert 102 in ids
    names = {p.name for p in providers}
    assert "Soheil" in names
    assert "Nadeem" in names

    service = db_session.query(Service).filter(
        Service.clinic_id == MARKET_MALL_CLINIC_ID, Service.id == 700
    ).first()
    assert service is not None
    assert service.name == "General Consultation"

    blocks = db_session.query(ProviderBusyBlock).filter(
        ProviderBusyBlock.clinic_id == MARKET_MALL_CLINIC_ID
    ).all()
    assert len(blocks) == 22

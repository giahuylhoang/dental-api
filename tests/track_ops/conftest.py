"""Fixtures for track_ops tests."""
import os

for _var in ("BOOKING_NOTIFICATION_TO", "SMS_DELAY_SECONDS", "SMTP_DEPLOY_VERIFY_TO"):
    os.environ.pop(_var, None)
os.environ["SEND_BOOKING_SMS"] = "false"
os.environ["SEND_CLINIC_BOOKING_EMAIL"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from database.models import Clinic, Lead, Patient, Provider, Service, DEFAULT_CLINIC_ID
import database.models  # noqa
import database.ops.models  # noqa

from api.main import app
import clients.sms_client as _sms
import clients.email_client as _email

_sms.SMS_DELAY_SECONDS = 0
_sms.SEND_BOOKING_SMS = False
_email.SEND_CLINIC_BOOKING_EMAIL = False

SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    for var in ("BOOKING_NOTIFICATION_TO", "SMS_DELAY_SECONDS", "SMTP_DEPLOY_VERIFY_TO"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SEND_BOOKING_SMS", "false")
    monkeypatch.setenv("SEND_CLINIC_BOOKING_EMAIL", "false")
    monkeypatch.setattr(_sms, "SMS_DELAY_SECONDS", 0)
    monkeypatch.setattr(_sms, "SEND_BOOKING_SMS", False)
    monkeypatch.setattr(_email, "SEND_CLINIC_BOOKING_EMAIL", False)


# Tables whose column types (e.g. pgvector.Vector, PG JSONB) cannot compile on
# SQLite. RAG features are exercised by the `pg_engine`/`pg_db_session`/`pg_client`
# fixtures, which run against the real Postgres + pgvector. Keep this set tight.
_SQLITE_SKIP_TABLES = {"rag_docs", "clinic_routing"}


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sqlite_tables = [
        t for t in Base.metadata.sorted_tables if t.name not in _SQLITE_SKIP_TABLES
    ]
    Base.metadata.create_all(bind=engine, tables=sqlite_tables)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()

    if not session.query(Clinic).filter(Clinic.id == DEFAULT_CLINIC_ID).first():
        session.add(Clinic(
            id=DEFAULT_CLINIC_ID,
            name="Test Clinic",
            timezone="America/Edmonton",
            working_hour_start=9,
            working_hour_end=17,
        ))
        session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        session.close()


@pytest.fixture(scope="function")
def client_market_mall(client, db_session):
    from scripts.init_database import seed_market_mall_denture
    seed_market_mall_denture(db_session)
    db_session.commit()
    yield client


@pytest.fixture(scope="function")
def seed_billing(client, db_session):
    """Create a patient, invoice with 3 lines, and a partial payment."""
    from database.ops.models import Invoice, InvoiceLine, Payment
    from decimal import Decimal

    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Bill", last_name="Test", phone="5550001")
    db_session.add(patient)
    db_session.flush()

    inv = Invoice(
        clinic_id=DEFAULT_CLINIC_ID,
        patient_id=patient.id,
        status="draft",
        subtotal=Decimal("300.00"),
        gst=Decimal("15.00"),
        total=Decimal("315.00"),
        balance=Decimal("315.00"),
        currency="CAD",
    )
    db_session.add(inv)
    db_session.flush()

    for i, (code, qty, price) in enumerate([("71201", 1, 100.0), ("71202", 2, 75.0), ("71203", 1, 50.0)]):
        db_session.add(InvoiceLine(
            invoice_id=inv.id,
            sequence=i + 1,
            procedure_code=code,
            qty=qty,
            unit_price=Decimal(str(price)),
            total=Decimal(str(price * qty)),
        ))

    payment = Payment(invoice_id=inv.id, method="cash", amount=Decimal("100.00"))
    db_session.add(payment)
    db_session.commit()

    yield {"patient": patient, "invoice": inv, "payment": payment}

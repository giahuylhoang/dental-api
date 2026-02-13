"""
Migration script: SQLite to PostgreSQL

This script migrates data from SQLite (dental_clinic.db) to PostgreSQL.

Usage:
    # Option 1: Set PostgreSQL connection string as environment variable
    export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
    
    # Option 2: Save in .env.local file (recommended)
    # DATABASE_URL="postgresql://user:pass@host:5432/dbname"
    
    # Run migration
    python scripts/migrate_sqlite_to_postgres.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.local or .env
env_files = [
    project_root / ".env.local",
    project_root / ".env",
    Path.cwd() / ".env.local",
    Path.cwd() / ".env",
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from: {env_file}")
        break

import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, UTC

# Import models
from database.connection import Base, engine as pg_engine, SessionLocal
from database.models import (
    Patient, Appointment, Doctor, Service, Lead,
    AppointmentStatus, LeadStatus
)


def get_sqlite_connection(sqlite_path: str = "dental_clinic.db"):
    """Connect to SQLite database."""
    # Try project root first
    sqlite_paths = [
        sqlite_path,
        os.path.join(project_root.parent, sqlite_path),
        os.path.join(os.getcwd(), sqlite_path),
    ]
    
    for path in sqlite_paths:
        if os.path.exists(path):
            print(f"✓ Found SQLite database: {path}")
            return sqlite3.connect(path)
    
    raise FileNotFoundError(f"SQLite database not found. Tried: {sqlite_paths}")


def create_postgres_tables():
    """Create tables in PostgreSQL."""
    print("\n📋 Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=pg_engine)
    print("✓ Tables created")


def migrate_doctors(sqlite_conn, pg_session: Session):
    """Migrate doctors table."""
    print("\n👨‍⚕️ Migrating doctors...")
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT id, name, specialty, is_active FROM doctors")
    
    doctors = cursor.fetchall()
    migrated = 0
    
    for doctor_data in doctors:
        doctor_id, name, specialty, is_active = doctor_data
        # Check if already exists
        existing = pg_session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if existing:
            print(f"  ⚠️  Doctor {name} (ID: {doctor_id}) already exists, skipping")
            continue
        
        doctor = Doctor(
            id=doctor_id,
            name=name,
            specialty=specialty or "General",
            is_active=bool(is_active) if is_active is not None else True
        )
        pg_session.add(doctor)
        migrated += 1
    
    pg_session.commit()
    print(f"✓ Migrated {migrated} doctors")


def migrate_services(sqlite_conn, pg_session: Session):
    """Migrate services table."""
    print("\n🦷 Migrating services...")
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, name, description, duration_min, base_price 
        FROM services
    """)
    
    services = cursor.fetchall()
    migrated = 0
    
    for service_data in services:
        service_id, name, description, duration_min, base_price = service_data
        # Check if already exists
        existing = pg_session.query(Service).filter(Service.id == service_id).first()
        if existing:
            print(f"  ⚠️  Service {name} (ID: {service_id}) already exists, skipping")
            continue
        
        service = Service(
            id=service_id,
            name=name,
            description=description,
            duration_min=duration_min or 30,
            base_price=float(base_price) if base_price else None
        )
        pg_session.add(service)
        migrated += 1
    
    pg_session.commit()
    print(f"✓ Migrated {migrated} services")


def migrate_patients(sqlite_conn, pg_session: Session):
    """Migrate patients table."""
    print("\n👤 Migrating patients...")
    cursor = sqlite_conn.cursor()
    
    # Check which columns exist in SQLite
    cursor.execute("PRAGMA table_info(patients)")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]
    
    # Build SELECT query based on available columns
    base_columns = ["id", "first_name", "last_name", "dob", "phone", "email", 
                    "insurance_provider", "is_minor", "guardian_name", 
                    "guardian_contact", "consent_approved"]
    
    select_columns = []
    for col in base_columns:
        if col in available_columns:
            select_columns.append(col)
    
    # Add optional timestamp columns if they exist
    if "created_at" in available_columns:
        select_columns.append("created_at")
    if "updated_at" in available_columns:
        select_columns.append("updated_at")
    
    query = f"SELECT {', '.join(select_columns)} FROM patients"
    cursor.execute(query)
    
    patients = cursor.fetchall()
    migrated = 0
    
    # Create a mapping of column index to name
    col_map = {i: col for i, col in enumerate(select_columns)}
    
    for patient_data in patients:
        # Create a dictionary from the row data
        patient_dict = {col_map[i]: val for i, val in enumerate(patient_data)}
        
        patient_id = patient_dict.get("id")
        first_name = patient_dict.get("first_name")
        last_name = patient_dict.get("last_name")
        dob = patient_dict.get("dob")
        phone = patient_dict.get("phone")
        email = patient_dict.get("email")
        insurance_provider = patient_dict.get("insurance_provider")
        is_minor = patient_dict.get("is_minor")
        guardian_name = patient_dict.get("guardian_name")
        guardian_contact = patient_dict.get("guardian_contact")
        consent_approved = patient_dict.get("consent_approved")
        created_at = patient_dict.get("created_at")
        updated_at = patient_dict.get("updated_at")
        
        # Check if already exists
        existing = pg_session.query(Patient).filter(Patient.id == patient_id).first()
        if existing:
            print(f"  ⚠️  Patient {first_name} {last_name} (ID: {patient_id}) already exists, skipping")
            continue
        
        # Convert date strings to date objects
        dob_date = None
        if dob:
            if isinstance(dob, str):
                try:
                    dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                except:
                    try:
                        dob_date = datetime.strptime(dob, '%Y-%m-%d %H:%M:%S').date()
                    except:
                        print(f"  ⚠️  Could not parse DOB for patient {patient_id}: {dob}")
            else:
                dob_date = dob
        
        created_at_dt = None
        if created_at:
            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = created_at
        
        updated_at_dt = None
        if updated_at:
            if isinstance(updated_at, str):
                updated_at_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated_at_dt = updated_at
        
        # Patient model only has created_at, not updated_at
        patient = Patient(
            id=patient_id,
            first_name=first_name,
            last_name=last_name,
            dob=dob_date,
            phone=phone,
            email=email,
            insurance_provider=insurance_provider,
            is_minor=bool(is_minor) if is_minor is not None else False,
            guardian_name=guardian_name,
            guardian_contact=guardian_contact,
            consent_approved=bool(consent_approved) if consent_approved is not None else False,
            created_at=created_at_dt or datetime.now(UTC)
        )
        pg_session.add(patient)
        migrated += 1
    
    pg_session.commit()
    print(f"✓ Migrated {migrated} patients")


def migrate_appointments(sqlite_conn, pg_session: Session):
    """Migrate appointments table."""
    print("\n📅 Migrating appointments...")
    cursor = sqlite_conn.cursor()
    
    # Check which columns exist in SQLite
    cursor.execute("PRAGMA table_info(appointments)")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]
    
    # Build SELECT query based on available columns
    base_columns = ["id", "patient_id", "doctor_id", "service_id", "start_time", "end_time",
                    "reason_note", "status", "calendar_event_id"]
    
    select_columns = []
    for col in base_columns:
        if col in available_columns:
            select_columns.append(col)
    
    # Add optional timestamp columns if they exist
    if "created_at" in available_columns:
        select_columns.append("created_at")
    if "updated_at" in available_columns:
        select_columns.append("updated_at")
    
    query = f"SELECT {', '.join(select_columns)} FROM appointments"
    cursor.execute(query)
    
    appointments = cursor.fetchall()
    migrated = 0
    
    # Create a mapping of column index to name
    col_map = {i: col for i, col in enumerate(select_columns)}
    
    for apt_data in appointments:
        # Create a dictionary from the row data
        apt_dict = {col_map[i]: val for i, val in enumerate(apt_data)}
        
        apt_id = apt_dict.get("id")
        patient_id = apt_dict.get("patient_id")
        doctor_id = apt_dict.get("doctor_id")
        service_id = apt_dict.get("service_id")
        start_time = apt_dict.get("start_time")
        end_time = apt_dict.get("end_time")
        reason_note = apt_dict.get("reason_note")
        status = apt_dict.get("status")
        calendar_event_id = apt_dict.get("calendar_event_id")
        created_at = apt_dict.get("created_at")
        updated_at = apt_dict.get("updated_at")
        
        # Check if already exists
        existing = pg_session.query(Appointment).filter(Appointment.id == apt_id).first()
        if existing:
            print(f"  ⚠️  Appointment {apt_id} already exists, skipping")
            continue
        
        # Convert datetime strings
        start_time_dt = None
        if start_time:
            if isinstance(start_time, str):
                start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_time_dt = start_time
        
        end_time_dt = None
        if end_time:
            if isinstance(end_time, str):
                end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_time_dt = end_time
        
        # Convert status string to enum
        status_enum = AppointmentStatus.PENDING
        if status:
            try:
                status_enum = AppointmentStatus(status.upper())
            except ValueError:
                print(f"  ⚠️  Unknown status '{status}' for appointment {apt_id}, using PENDING")
                status_enum = AppointmentStatus.PENDING
        
        created_at_dt = None
        if created_at:
            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = created_at
        
        updated_at_dt = None
        if updated_at:
            if isinstance(updated_at, str):
                updated_at_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated_at_dt = updated_at
        
        appointment = Appointment(
            id=apt_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            service_id=service_id,
            start_time=start_time_dt,
            end_time=end_time_dt,
            reason_note=reason_note,
            status=status_enum,
            calendar_event_id=calendar_event_id,
            created_at=created_at_dt or datetime.now(UTC),
            updated_at=updated_at_dt or datetime.now(UTC)
        )
        pg_session.add(appointment)
        migrated += 1
    
    pg_session.commit()
    print(f"✓ Migrated {migrated} appointments")


def migrate_leads(sqlite_conn, pg_session: Session):
    """Migrate leads table."""
    print("\n📞 Migrating leads...")
    cursor = sqlite_conn.cursor()
    
    # Check if leads table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='leads'
    """)
    if not cursor.fetchone():
        print("  ⚠️  Leads table not found in SQLite, skipping")
        return
    
    # Check which columns exist in SQLite
    cursor.execute("PRAGMA table_info(leads)")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]
    
    # Build SELECT query based on available columns
    base_columns = ["id", "name", "phone", "email", "source", "status", "notes"]
    
    select_columns = []
    for col in base_columns:
        if col in available_columns:
            select_columns.append(col)
    
    # Add optional timestamp columns if they exist
    if "created_at" in available_columns:
        select_columns.append("created_at")
    if "updated_at" in available_columns:
        select_columns.append("updated_at")
    
    query = f"SELECT {', '.join(select_columns)} FROM leads"
    cursor.execute(query)
    
    leads = cursor.fetchall()
    migrated = 0
    
    # Create a mapping of column index to name
    col_map = {i: col for i, col in enumerate(select_columns)}
    
    for lead_data in leads:
        # Create a dictionary from the row data
        lead_dict = {col_map[i]: val for i, val in enumerate(lead_data)}
        
        lead_id = lead_dict.get("id")
        name = lead_dict.get("name")
        phone = lead_dict.get("phone")
        email = lead_dict.get("email")
        source = lead_dict.get("source")
        status = lead_dict.get("status")
        notes = lead_dict.get("notes")
        created_at = lead_dict.get("created_at")
        updated_at = lead_dict.get("updated_at")
        
        # Check if already exists
        existing = pg_session.query(Lead).filter(Lead.id == lead_id).first()
        if existing:
            print(f"  ⚠️  Lead {name} (ID: {lead_id}) already exists, skipping")
            continue
        
        # Convert status string to enum
        status_enum = LeadStatus.NEW
        if status:
            try:
                status_enum = LeadStatus(status.upper())
            except ValueError:
                print(f"  ⚠️  Unknown status '{status}' for lead {lead_id}, using NEW")
                status_enum = LeadStatus.NEW
        
        created_at_dt = None
        if created_at:
            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = created_at
        
        updated_at_dt = None
        if updated_at:
            if isinstance(updated_at, str):
                updated_at_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated_at_dt = updated_at
        
        lead = Lead(
            id=lead_id,
            name=name,
            phone=phone,
            email=email,
            source=source,
            status=status_enum,
            notes=notes,
            created_at=created_at_dt or datetime.now(UTC),
            updated_at=updated_at_dt or datetime.now(UTC)
        )
        pg_session.add(lead)
        migrated += 1
    
    pg_session.commit()
    print(f"✓ Migrated {migrated} leads")


def verify_migration(sqlite_conn, pg_session: Session):
    """Verify migration by comparing record counts."""
    print("\n🔍 Verifying migration...")
    
    cursor = sqlite_conn.cursor()
    
    tables = [
        ("doctors", Doctor),
        ("services", Service),
        ("patients", Patient),
        ("appointments", Appointment),
    ]
    
    # Check leads table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='leads'
    """)
    if cursor.fetchone():
        tables.append(("leads", Lead))
    
    all_match = True
    for table_name, model in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = cursor.fetchone()[0]
        pg_count = pg_session.query(model).count()
        
        status = "✓" if sqlite_count == pg_count else "✗"
        print(f"  {status} {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        
        if sqlite_count != pg_count:
            all_match = False
    
    if all_match:
        print("\n✅ Migration verification passed!")
    else:
        print("\n⚠️  Migration verification found discrepancies. Please review.")
    
    return all_match


def main():
    """Main migration function."""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)
    
    # Check PostgreSQL connection
    pg_url = os.getenv("DATABASE_URL")
    if not pg_url:
        print("\n❌ Error: DATABASE_URL environment variable not set")
        print("\nSet it with one of these methods:")
        print("  1. Export as environment variable:")
        print("     export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        print("  2. Add to .env.local file:")
        print("     DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        print("\nThe script will automatically load from .env.local if it exists.")
        sys.exit(1)
    
    if "sqlite" in pg_url.lower():
        print("\n❌ Error: DATABASE_URL points to SQLite, not PostgreSQL")
        print("Please set DATABASE_URL to a PostgreSQL connection string")
        sys.exit(1)
    
    print(f"\n📊 PostgreSQL URL: {pg_url.split('@')[1] if '@' in pg_url else 'configured'}")
    
    # Connect to SQLite
    try:
        sqlite_conn = get_sqlite_connection()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    # Connect to PostgreSQL
    try:
        pg_session = SessionLocal()
        # Test connection
        pg_session.execute(text("SELECT 1"))
        print("✓ PostgreSQL connection successful")
    except Exception as e:
        print(f"\n❌ Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    
    try:
        # Create tables
        create_postgres_tables()
        
        # Migrate data
        migrate_doctors(sqlite_conn, pg_session)
        migrate_services(sqlite_conn, pg_session)
        migrate_patients(sqlite_conn, pg_session)
        migrate_appointments(sqlite_conn, pg_session)
        migrate_leads(sqlite_conn, pg_session)
        
        # Verify
        verify_migration(sqlite_conn, pg_session)
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        pg_session.rollback()
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_session.close()


if __name__ == "__main__":
    main()

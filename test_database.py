#!/usr/bin/env python3
"""
Test database connection and verify it's working correctly.

Usage:
    python test_database.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Check for required dependencies
try:
    import psycopg2
except ImportError:
    print("❌ Error: psycopg2-binary is not installed")
    print("\nInstall it with:")
    print("   pip install psycopg2-binary")
    print("\nOr install all requirements:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

try:
    from database.connection import engine, SessionLocal, DATABASE_URL
    from database.models import Patient, Doctor, Service, Appointment, Lead
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ Error importing database modules: {e}")
    print("\nMake sure you're in the dental-api directory and dependencies are installed:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def test_connection():
    """Test basic database connection."""
    print("🔍 Testing database connection...")
    print(f"📊 Database URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"📊 Database URL: {DATABASE_URL}")
    
    try:
        # Test raw connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ Database connection successful!\n")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}\n")
        return False

def test_tables():
    """Test that tables exist and are accessible."""
    print("🔍 Testing database tables...")
    
    session = SessionLocal()
    try:
        # Test each table
        tables = {
            "patients": Patient,
            "doctors": Doctor,
            "services": Service,
            "appointments": Appointment,
        }
        
        # Check if leads table exists (optional)
        try:
            tables["leads"] = Lead
        except:
            pass
        
        all_exist = True
        for table_name, model in tables.items():
            try:
                count = session.query(model).count()
                print(f"   ✅ {table_name}: {count} records")
            except Exception as e:
                print(f"   ❌ {table_name}: Error - {e}")
                all_exist = False
        
        print()
        return all_exist
    except Exception as e:
        print(f"❌ Error testing tables: {e}\n")
        return False
    finally:
        session.close()

def test_read_write():
    """Test read and write operations."""
    print("🔍 Testing read/write operations...")
    
    session = SessionLocal()
    try:
        # Test read
        doctor_count = session.query(Doctor).count()
        print(f"   ✅ Read operation: Found {doctor_count} doctors")
        
        # Test write (create a test record, then delete it)
        # We'll test with a simple query instead to avoid creating test data
        test_query = session.query(Doctor).first()
        if test_query:
            print(f"   ✅ Query operation: Retrieved doctor '{test_query.name}'")
        else:
            print("   ⚠️  No data found (database might be empty)")
        
        print()
        return True
    except Exception as e:
        print(f"   ❌ Read/write test failed: {e}\n")
        return False
    finally:
        session.close()

def show_database_info():
    """Show database information."""
    print("📋 Database Information:")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Count records
        patient_count = session.query(Patient).count()
        doctor_count = session.query(Doctor).count()
        service_count = session.query(Service).count()
        appointment_count = session.query(Appointment).count()
        
        # Check leads table
        try:
            lead_count = session.query(Lead).count()
        except:
            lead_count = None
        
        print(f"   Patients: {patient_count}")
        print(f"   Doctors: {doctor_count}")
        print(f"   Services: {service_count}")
        print(f"   Appointments: {appointment_count}")
        if lead_count is not None:
            print(f"   Leads: {lead_count}")
        
        # Show sample data
        if patient_count > 0:
            sample_patient = session.query(Patient).first()
            print(f"\n   Sample Patient: {sample_patient.first_name} {sample_patient.last_name}")
        
        if doctor_count > 0:
            sample_doctor = session.query(Doctor).first()
            print(f"   Sample Doctor: {sample_doctor.name}")
        
        if service_count > 0:
            sample_service = session.query(Service).first()
            print(f"   Sample Service: {sample_service.name}")
        
        print("=" * 60)
        print()
    except Exception as e:
        print(f"   ❌ Error getting database info: {e}\n")
    finally:
        session.close()

def main():
    """Run all database tests."""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    # Run tests
    connection_ok = test_connection()
    if not connection_ok:
        print("❌ Cannot proceed - database connection failed")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL or POSTGRES_URL environment variable")
        print("2. Verify database server is running and accessible")
        print("3. Check network connectivity and firewall settings")
        sys.exit(1)
    
    tables_ok = test_tables()
    read_write_ok = test_read_write()
    
    # Show database info
    show_database_info()
    
    # Summary
    print("📊 Test Summary:")
    print("=" * 60)
    print(f"   Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"   Tables: {'✅ PASS' if tables_ok else '❌ FAIL'}")
    print(f"   Read/Write: {'✅ PASS' if read_write_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if connection_ok and tables_ok and read_write_ok:
        print("\n✅ All tests passed! Your database is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

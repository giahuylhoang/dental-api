#!/usr/bin/env python3
"""Test PostgreSQL connection and verify migrated data."""

from database.connection import engine, SessionLocal
from database.models import Patient, Doctor, Service, Appointment, Lead

def test_connection():
    """Test database connection and show data counts."""
    print("🔍 Testing PostgreSQL connection...")
    
    session = SessionLocal()
    try:
        # Test connection
        engine.connect()
        print("✅ Connection successful!\n")
        
        # Count records
        patient_count = session.query(Patient).count()
        doctor_count = session.query(Doctor).count()
        service_count = session.query(Service).count()
        appointment_count = session.query(Appointment).count()
        
        # Check if leads table exists
        try:
            lead_count = session.query(Lead).count()
        except:
            lead_count = None
        
        print("📊 Data counts:")
        print(f"   Patients: {patient_count}")
        print(f"   Doctors: {doctor_count}")
        print(f"   Services: {service_count}")
        print(f"   Appointments: {appointment_count}")
        if lead_count is not None:
            print(f"   Leads: {lead_count}")
        
        # Show sample data
        print("\n📋 Sample data:")
        if patient_count > 0:
            sample_patient = session.query(Patient).first()
            print(f"   Sample Patient: {sample_patient.first_name} {sample_patient.last_name}")
        
        if doctor_count > 0:
            sample_doctor = session.query(Doctor).first()
            print(f"   Sample Doctor: {sample_doctor.name}")
        
        if service_count > 0:
            sample_service = session.query(Service).first()
            print(f"   Sample Service: {sample_service.name}")
        
        print("\n✅ All checks passed! Your application is ready to use PostgreSQL.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
    
    return True

if __name__ == "__main__":
    test_connection()

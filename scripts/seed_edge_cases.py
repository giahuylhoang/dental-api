"""Edge case seeders for testing."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database.models import Clinic, Patient, Appointment, AppointmentStatus, Provider, Service


def seed_empty(db: Session):
    """Seed an empty clinic with no data."""
    clinic = Clinic(id="empty-clinic", display_name="Empty Clinic", timezone="America/Edmonton")
    db.add(clinic)
    db.commit()
    return clinic


def seed_maxed(db: Session):
    """Seed a clinic with 1k patients, 5k appointments, 200 plans."""
    clinic = Clinic(id="maxed-clinic", display_name="Maxed Clinic", timezone="America/Edmonton")
    db.add(clinic)
    db.flush()
    
    # Add a provider
    provider = Provider(id=9001, clinic_id=clinic.id, name="Dr Max", title="Dr", is_active=True)
    db.add(provider)
    
    # Add a service
    service = Service(id=9001, clinic_id=clinic.id, name="General", duration_min=30, base_price=100)
    db.add(service)
    db.flush()
    
    # Add 1k patients
    for i in range(1000):
        patient = Patient(
            id=f"P-MAX-{i:04d}",
            clinic_id=clinic.id,
            first_name=f"Patient{i}",
            last_name=f"Max{i}",
            phone=f"555-{i:04d}",
        )
        db.add(patient)
    
    db.flush()
    
    # Add 5k appointments (spread across patients)
    base_time = datetime.utcnow()
    for i in range(5000):
        patient_idx = i % 1000
        appt = Appointment(
            clinic_id=clinic.id,
            patient_id=f"P-MAX-{patient_idx:04d}",
            provider_id=9001,
            service_id=9001,
            start_time=base_time + timedelta(hours=i),
            end_time=base_time + timedelta(hours=i, minutes=30),
            status=AppointmentStatus.CONFIRMED,
        )
        db.add(appt)
    
    db.commit()
    return clinic


def seed_adversarial(db: Session):
    """Seed a clinic with unicode, long strings, SQL-quote chars."""
    clinic = Clinic(id="adversarial-clinic", display_name="Adversarial Clinic", timezone="America/Edmonton")
    db.add(clinic)
    db.flush()
    
    # Unicode names
    patients = [
        ("José", "García"),
        ("田中", "太郎"),
        ("Müller", "Hans"),
        ("O'Brien", "Patrick"),
        ("Test", "User'; DROP TABLE patients; --"),
        ("Emoji", "Test 🦷💉"),
    ]
    
    for i, (first, last) in enumerate(patients):
        patient = Patient(
            id=f"P-ADV-{i:04d}",
            clinic_id=clinic.id,
            first_name=first,
            last_name=last,
            phone=f"555-{i:04d}",
        )
        db.add(patient)
    
    # Very long string
    long_patient = Patient(
        id="P-ADV-LONG",
        clinic_id=clinic.id,
        first_name="A" * 200,
        last_name="B" * 200,
        phone="555-9999",
    )
    db.add(long_patient)
    
    db.commit()
    return clinic


def seed_concurrent_test(db: Session):
    """Seed a clinic for concurrent booking tests."""
    clinic = Clinic(id="concurrent-clinic", display_name="Concurrent Clinic", timezone="America/Edmonton")
    db.add(clinic)
    db.flush()
    
    provider = Provider(id=9002, clinic_id=clinic.id, name="Dr Concurrent", title="Dr", is_active=True)
    db.add(provider)
    
    service = Service(id=9002, clinic_id=clinic.id, name="Concurrent Service", duration_min=30, base_price=100)
    db.add(service)
    
    patient = Patient(
        id="P-CONC-0001",
        clinic_id=clinic.id,
        first_name="Concurrent",
        last_name="Patient",
        phone="555-0001",
    )
    db.add(patient)
    
    db.commit()
    return clinic

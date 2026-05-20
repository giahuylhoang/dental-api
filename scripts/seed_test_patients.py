"""
Seed 20 test patients with appointments for the Market Mall Denture Clinic.

Run: uv run python scripts/seed_test_patients.py
Safe to run multiple times — checks before inserting.

These patients are used by dental-agent test suites.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, date, time
from database.connection import SessionLocal, init_db
from database.models import Patient, Appointment, Provider

CLINIC_ID = "market-mall-denture"
MARKER_PHONE_PREFIX = "40355500"  # All test patients start with this

TEST_PATIENTS = [
    {"first_name": "Alice",   "last_name": "Thompson", "phone": "4035550001", "dob": "1985-03-15", "email": "alice.t@test.com"},
    {"first_name": "Bob",     "last_name": "Martinez", "phone": "4035550002", "dob": "1990-07-22", "email": "bob.m@test.com"},
    {"first_name": "Carol",   "last_name": "Chen",     "phone": "4035550003", "dob": "1978-11-08", "email": "carol.c@test.com"},
    {"first_name": "David",   "last_name": "Singh",    "phone": "4035550004", "dob": "1965-01-30", "email": "david.s@test.com"},
    {"first_name": "Emma",    "last_name": "Wilson",   "phone": "4035550005", "dob": "1992-06-14", "email": "emma.w@test.com"},
    {"first_name": "Frank",   "last_name": "Nguyen",   "phone": "4035550006", "dob": "1988-09-03", "email": "frank.n@test.com"},
    {"first_name": "Grace",   "last_name": "Patel",    "phone": "4035550007", "dob": "1975-12-25", "email": "grace.p@test.com"},
    {"first_name": "Henry",   "last_name": "Kim",      "phone": "4035550008", "dob": "1982-04-17", "email": "henry.k@test.com"},
    {"first_name": "Iris",    "last_name": "Brown",    "phone": "4035550009", "dob": "1995-08-29", "email": "iris.b@test.com"},
    {"first_name": "Jack",    "last_name": "Garcia",   "phone": "4035550010", "dob": "1970-02-11", "email": "jack.g@test.com"},
    {"first_name": "Karen",   "last_name": "Lee",      "phone": "4035550011", "dob": "1987-05-06", "email": "karen.l@test.com"},
    {"first_name": "Leo",     "last_name": "Anderson", "phone": "4035550012", "dob": "1993-10-19", "email": "leo.a@test.com"},
    {"first_name": "Maria",   "last_name": "Russo",    "phone": "4035550013", "dob": "1968-07-04", "email": "maria.r@test.com"},
    {"first_name": "Nathan",  "last_name": "Clark",    "phone": "4035550014", "dob": "1991-01-23", "email": "nathan.c@test.com"},
    {"first_name": "Olivia",  "last_name": "Wright",   "phone": "4035550015", "dob": "1983-11-30", "email": "olivia.w@test.com"},
    {"first_name": "Peter",   "last_name": "Hall",     "phone": "4035550016", "dob": "1976-03-08", "email": "peter.h@test.com"},
    {"first_name": "Quinn",   "last_name": "Adams",    "phone": "4035550017", "dob": "1998-09-12", "email": "quinn.a@test.com"},
    {"first_name": "Rosa",    "last_name": "Diaz",     "phone": "4035550018", "dob": "1972-06-27", "email": "rosa.d@test.com"},
    {"first_name": "Sam",     "last_name": "Taylor",   "phone": "4035550019", "dob": "1989-12-01", "email": "sam.t@test.com"},
    {"first_name": "Tina",    "last_name": "Wang",     "phone": "4035550020", "dob": "1994-04-15", "email": "tina.w@test.com"},
]


def seed():
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(Patient).filter(Patient.phone.like(f"{MARKER_PHONE_PREFIX}%"), Patient.clinic_id == CLINIC_ID).count()
        if existing >= 20:
            print(f"Already seeded: {existing} test patients exist. Skipping.")
            return

        # Get providers
        providers = db.query(Provider).filter(Provider.clinic_id == CLINIC_ID).all()
        if not providers:
            print("ERROR: No providers found for market-mall-denture. Run sync_db.py first.")
            return
        provider_ids = [p.id for p in providers]

        print(f"Seeding {len(TEST_PATIENTS)} test patients for clinic '{CLINIC_ID}'...")

        # Create patients
        created_patients = []
        for p_data in TEST_PATIENTS:
            patient = Patient(
                clinic_id=CLINIC_ID,
                first_name=p_data["first_name"],
                last_name=p_data["last_name"],
                phone=p_data["phone"],
                dob=date.fromisoformat(p_data["dob"]),
                email=p_data["email"],
                consent_approved=True,
            )
            db.add(patient)
            db.flush()  # Get the ID
            created_patients.append(patient)
            print(f"  Patient: {p_data['first_name']} {p_data['last_name']} (phone: {p_data['phone']}, id: {patient.id})")

        # Create appointments for first 10 patients (some have appointments to test cancel/reschedule)
        base_date = date.today() + timedelta(days=3)
        while base_date.weekday() >= 5:
            base_date += timedelta(days=1)

        for i, patient in enumerate(created_patients[:10]):
            # Spread appointments across next 2 weeks
            apt_date = base_date + timedelta(days=(i % 5) * 2)
            while apt_date.weekday() >= 5:
                apt_date += timedelta(days=1)

            start_dt = datetime.combine(apt_date, time(9 + (i % 4), (i % 2) * 30))
            end_dt = start_dt + timedelta(minutes=30)
            prov_id = provider_ids[i % len(provider_ids)]

            apt = Appointment(
                clinic_id=CLINIC_ID,
                patient_id=str(patient.id),
                provider_id=prov_id,
                service_id=700,
                start_time=start_dt,
                end_time=end_dt,
                reason_note="General Consultation",
                status="SCHEDULED",
            )
            db.add(apt)
            print(f"  Appointment: {patient.first_name} {patient.last_name} on {apt_date} at {start_dt.strftime('%H:%M')} (id: will be generated)")

        db.commit()
        print(f"\nDone! Created {len(created_patients)} patients and {min(10, len(created_patients))} appointments.")
        print("\n--- TEST PATIENT REFERENCE ---")
        print("Use these for dental-agent tests:")
        for p_data in TEST_PATIENTS:
            print(f"  {p_data['first_name']:8s} {p_data['last_name']:10s} phone={p_data['phone']} dob={p_data['dob']}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

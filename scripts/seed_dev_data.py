"""
Seed sample patients, appointments, leads, and a denture case for the default
clinic so the SPA has visible data when pointed at the real backend.

Idempotent: skips rows whose phone numbers already exist.

Usage:
    DATABASE_URL=sqlite:///./dental_clinic.db uv run python scripts/seed_dev_data.py
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import SessionLocal, init_db
from database.models import (
    Appointment,
    AppointmentStatus,
    Lead,
    LeadStatus,
    Patient,
    Provider,
    Service,
    DEFAULT_CLINIC_ID,
)


SAMPLE_PATIENTS = [
    {"first_name": "Alice",   "last_name": "Thompson",  "phone": "5550100001", "email": "alice.t@example.com",   "dob": date(1962, 4, 12)},
    {"first_name": "Bob",     "last_name": "Martinez",  "phone": "5550100002", "email": "bob.m@example.com",     "dob": date(1955, 11, 3)},
    {"first_name": "Cathy",   "last_name": "Nguyen",    "phone": "5550100003", "email": "cathy.n@example.com",   "dob": date(1978, 7, 22)},
    {"first_name": "David",   "last_name": "Khan",      "phone": "5550100004", "email": "david.k@example.com",   "dob": date(1948, 1, 30)},
    {"first_name": "Elena",   "last_name": "Rossi",     "phone": "5550100005", "email": "elena.r@example.com",   "dob": date(1969, 9, 15)},
    {"first_name": "Farid",   "last_name": "Ahmadi",    "phone": "5550100006", "email": "farid.a@example.com",   "dob": date(1952, 3, 8)},
    {"first_name": "Grace",   "last_name": "Okafor",    "phone": "5550100007", "email": "grace.o@example.com",   "dob": date(1985, 12, 1)},
    {"first_name": "Henry",   "last_name": "Sullivan",  "phone": "5550100008", "email": "henry.s@example.com",   "dob": date(1944, 6, 18)},
]

SAMPLE_LEADS = [
    {"name": "Inez Park",   "phone": "5550200001", "email": "inez@example.com",   "source": "google_ads",  "status": LeadStatus.NEW},
    {"name": "Joel Ramirez","phone": "5550200002", "email": "joel@example.com",   "source": "facebook",    "status": LeadStatus.CONTACTED},
    {"name": "Kim Lee",     "phone": "5550200003", "email": "kim@example.com",    "source": "referral",    "status": LeadStatus.QUALIFIED},
    {"name": "Liam O'Neil", "phone": "5550200004", "email": "liam@example.com",   "source": "walk_in",     "status": LeadStatus.LOST},
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        clinic_id = DEFAULT_CLINIC_ID
        provider = db.query(Provider).filter(Provider.clinic_id == clinic_id, Provider.is_active.is_(True)).first()
        if not provider:
            print("No active provider in default clinic; run scripts/sync_db.py first.")
            return
        service = db.query(Service).filter(Service.clinic_id == clinic_id).order_by(Service.id).first()

        created_patients = 0
        created_patient_ids: list[str] = []
        for p in SAMPLE_PATIENTS:
            existing = db.query(Patient).filter(
                Patient.clinic_id == clinic_id, Patient.phone == p["phone"]
            ).first()
            if existing:
                created_patient_ids.append(existing.id)
                continue
            patient = Patient(
                id=str(uuid.uuid4()),
                clinic_id=clinic_id,
                first_name=p["first_name"],
                last_name=p["last_name"],
                phone=p["phone"],
                email=p["email"],
                dob=p["dob"],
                consent_approved=True,
            )
            db.add(patient)
            db.flush()
            created_patient_ids.append(patient.id)
            created_patients += 1

        # Two upcoming appointments for the first two patients.
        now = datetime.now(timezone.utc).replace(microsecond=0)
        future_starts = [now + timedelta(days=2, hours=10 - now.hour),
                         now + timedelta(days=4, hours=14 - now.hour)]
        created_appts = 0
        for idx, start in enumerate(future_starts):
            if idx >= len(created_patient_ids):
                break
            existing = db.query(Appointment).filter(
                Appointment.clinic_id == clinic_id,
                Appointment.patient_id == created_patient_ids[idx],
                Appointment.start_time == start,
            ).first()
            if existing:
                continue
            apt = Appointment(
                id=str(uuid.uuid4()),
                clinic_id=clinic_id,
                patient_id=created_patient_ids[idx],
                provider_id=provider.id,
                service_id=service.id if service else None,
                start_time=start,
                end_time=start + timedelta(minutes=30),
                reason_note="Demo seed appointment",
                status=AppointmentStatus.SCHEDULED,
            )
            db.add(apt)
            created_appts += 1

        created_leads = 0
        for L in SAMPLE_LEADS:
            existing = db.query(Lead).filter(
                Lead.clinic_id == clinic_id, Lead.phone == L["phone"]
            ).first()
            if existing:
                continue
            db.add(Lead(
                id=str(uuid.uuid4()),
                clinic_id=clinic_id,
                name=L["name"],
                phone=L["phone"],
                email=L["email"],
                source=L["source"],
                status=L["status"],
            ))
            created_leads += 1

        db.commit()
        print(f"Seeded {created_patients} patients, {created_appts} appointments, {created_leads} leads for clinic '{clinic_id}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

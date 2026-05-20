"""
Demo seed for AI Receptionist config + a few patients so the new Settings AI
tabs and Patients page have real data when the frontend boots against the
local FastAPI backend.

Idempotent: running this twice is safe — every insert is guarded by an
existence check on the natural key.

Run via:
    DATABASE_URL=sqlite:///./dental_clinic.db python scripts/seed_demo_ai.py
"""
from __future__ import annotations

import sys
import os
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import init_db, SessionLocal  # noqa: E402
from database.models import Clinic, Patient, Service, DEFAULT_CLINIC_ID  # noqa: E402
from database.ops.ai_config import (  # noqa: E402
    ClinicAiVoice,
    ClinicAiDisclosure,
    ServiceAiBookable,
    ClinicKnowledgeDoc,
)


KNOWLEDGE_SEED = [
    {
        "filename": "practice_info.md",
        "title": "Practice info — hours, address, parking",
        "body": (
            "# Practice info\n\n"
            "## Hours\nMonday–Friday 8:00 AM – 5:00 PM\nSaturday 9:00 AM – 2:00 PM\nSunday closed\n\n"
            "## Address\n1420 17 Ave SW, Calgary, AB T2T 0B9\n\n"
            "## Parking\nFree two-hour parking on 17 Ave. Underground parkade entrance off 14 St SW.\n\n"
            "## Phone\n403-555-0180 (front desk) · 403-555-0911 (after-hours emergency line)"
        ),
    },
    {
        "filename": "denture_faq.md",
        "title": "Denture FAQ — most common caller questions",
        "body": (
            "# Denture FAQ\n\n"
            "## Do I need a referral?\nNo — denturists can be seen without a dentist referral in Alberta.\n\n"
            "## How long does a complete denture take?\nFour to six visits over three to four weeks.\n\n"
            "## Does insurance cover dentures?\nMost plans cover 50–60% of complete dentures every 5 years.\n"
        ),
    },
    {
        "filename": "insurance_carriers.md",
        "title": "Accepted insurance carriers",
        "body": (
            "# Accepted insurance\n\n"
            "- Alberta Blue Cross\n- Sun Life\n- Manulife\n- Canada Life\n- Pacific Blue Cross\n"
            "- Alberta Health (AB Adult Dental Plan)\n"
        ),
    },
]

PATIENTS_SEED = [
    {"id": "P-018342", "first_name": "Alice", "last_name": "Stevens", "phone": "+14035550120", "email": "alice@example.com"},
    {"id": "P-018298", "first_name": "Marcus", "last_name": "Doan", "phone": "+15875550099", "email": "marcus@example.com"},
    {"id": "P-018501", "first_name": "Priya", "last_name": "Khanna", "phone": "+14035550103", "email": "priya@example.com"},
    {"id": "P-017901", "first_name": "Eli", "last_name": "Brouwer", "phone": "+14035550110", "email": "eli@example.com"},
    {"id": "P-018611", "first_name": "Sofía", "last_name": "Castillo", "phone": "+14035550111", "email": "sofia@example.com"},
    {"id": "P-016102", "first_name": "Daniel", "last_name": "Okafor", "phone": "+14035550112", "email": "daniel@example.com"},
]


def _word_count(text: str) -> int:
    import re
    return len(re.findall(r"\b\w+\b", text))


def seed_demo_ai_config(db, clinic_id: str = DEFAULT_CLINIC_ID) -> dict:
    """Idempotently seed AI config rows + a handful of demo patients.

    Returns a counter dict of what was inserted vs skipped.
    """
    counters = {"voice": "skipped", "disclosure": "skipped", "knowledge": 0,
                "patients": 0, "services_bookable": 0}

    if not db.query(Clinic).filter(Clinic.id == clinic_id).first():
        raise RuntimeError(f"Clinic {clinic_id!r} must be seeded before running seed_demo_ai")

    # Voice
    if not db.query(ClinicAiVoice).filter(ClinicAiVoice.clinic_id == clinic_id).first():
        db.add(ClinicAiVoice(
            clinic_id=clinic_id,
            assistant_name="Aurora",
            provider_title="Denturist",
            reason_question="What brings you in today?",
            language="en-CA",
        ))
        counters["voice"] = "inserted"

    # Disclosure
    if not db.query(ClinicAiDisclosure).filter(ClinicAiDisclosure.clinic_id == clinic_id).first():
        db.add(ClinicAiDisclosure(
            clinic_id=clinic_id,
            required=True,
            phrase=(
                "Hi, this is the AI receptionist for the clinic. I am not a human — "
                "I can book, reschedule, or transfer you to the front desk."
            ),
            last_reviewed_at=datetime.utcnow(),
        ))
        counters["disclosure"] = "inserted"

    # Knowledge docs
    for doc in KNOWLEDGE_SEED:
        existing = (
            db.query(ClinicKnowledgeDoc)
            .filter(
                ClinicKnowledgeDoc.clinic_id == clinic_id,
                ClinicKnowledgeDoc.filename == doc["filename"],
            )
            .first()
        )
        if existing is None:
            db.add(ClinicKnowledgeDoc(
                clinic_id=clinic_id,
                filename=doc["filename"],
                title=doc["title"],
                body=doc["body"],
                word_count=_word_count(doc["body"]),
            ))
            counters["knowledge"] += 1

    # Patients (only when the table is empty for this clinic, to keep the seed
    # safe for repeated runs against existing dev DBs).
    existing_patients = (
        db.query(Patient).filter(Patient.clinic_id == clinic_id).count()
    )
    if existing_patients == 0:
        for p in PATIENTS_SEED:
            db.add(Patient(
                id=p["id"],
                clinic_id=clinic_id,
                first_name=p["first_name"],
                last_name=p["last_name"],
                phone=p["phone"],
                email=p["email"],
            ))
            counters["patients"] += 1

    # Mark the first 3 services as AI-bookable (defaults are false).
    services = db.query(Service).filter(Service.clinic_id == clinic_id).order_by(Service.id).limit(3).all()
    for svc in services:
        existing = db.query(ServiceAiBookable).filter(ServiceAiBookable.service_id == svc.id).first()
        if existing is None:
            db.add(ServiceAiBookable(service_id=svc.id, clinic_id=clinic_id, bookable=True))
            counters["services_bookable"] += 1

    db.commit()
    return counters


def main():
    print("Seeding demo AI config + patients...")
    print("=" * 50)
    init_db()
    db = SessionLocal()
    try:
        counters = seed_demo_ai_config(db)
        for k, v in counters.items():
            print(f"  {k}: {v}")
    finally:
        db.close()
    print("=" * 50)
    print("Done.")


if __name__ == "__main__":
    main()

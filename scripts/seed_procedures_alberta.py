"""Seed Alberta CDA fee guide subset for denturist procedures. Idempotent."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal, Base, engine
import database.models  # noqa
import database.clinical.models  # noqa
from database.clinical.models import Procedure
from database.models import Clinic, DEFAULT_CLINIC_ID

PROCEDURES = [
    # Complete dentures
    ("51101", "Complete Upper Denture", 120, 1200.0, "prosthodontic"),
    ("51102", "Complete Lower Denture", 120, 1200.0, "prosthodontic"),
    # Partial dentures
    ("53101", "Partial Upper Denture (Cast Metal)", 90, 1500.0, "prosthodontic"),
    ("53102", "Partial Lower Denture (Cast Metal)", 90, 1500.0, "prosthodontic"),
    # Relines
    ("55301", "Reline Hard (Lab)", 60, 400.0, "prosthodontic"),
    ("55302", "Reline Soft (Lab)", 60, 450.0, "prosthodontic"),
    # Repairs
    ("52101", "Denture Repair - Simple", 30, 150.0, "prosthodontic"),
    ("52102", "Denture Repair - Complex", 60, 250.0, "prosthodontic"),
    ("52199", "Denture Repair - Other", 45, 200.0, "prosthodontic"),
    # Adjustments
    ("55101", "Denture Adjustment", 20, 75.0, "prosthodontic"),
    # Exam
    ("01101", "Complete Oral Examination", 30, 120.0, "diagnostic"),
    # X-rays
    ("02101", "Periapical Radiograph", 10, 35.0, "diagnostic"),
    ("02102", "Bitewing Radiograph", 10, 35.0, "diagnostic"),
]


def seed_procedures(clinic_id: str = DEFAULT_CLINIC_ID):
    db = SessionLocal()
    try:
        for code, name, duration, fee, category in PROCEDURES:
            existing = db.query(Procedure).filter(
                Procedure.clinic_id == clinic_id,
                Procedure.code == code,
            ).first()
            if not existing:
                db.add(Procedure(
                    clinic_id=clinic_id,
                    code=code,
                    name=name,
                    default_duration_min=duration,
                    default_fee=fee,
                    category=category,
                ))
        db.commit()
        print(f"Seeded {len(PROCEDURES)} procedures for clinic {clinic_id}")
    finally:
        db.close()


if __name__ == "__main__":
    clinic_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CLINIC_ID
    Base.metadata.create_all(bind=engine)
    seed_procedures(clinic_id)

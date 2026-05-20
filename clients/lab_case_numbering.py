"""Generate sequential lab case numbers: LC-YYYY-NNNN."""
from datetime import datetime
from sqlalchemy.orm import Session
from database.clinical.models import LabCase


def next_lab_case_number(session: Session, clinic_id: str) -> str:
    year = datetime.utcnow().year
    prefix = f"LC-{year}-"
    # Count existing cases for this clinic+year
    count = (
        session.query(LabCase)
        .filter(
            LabCase.clinic_id == clinic_id,
            LabCase.case_number.like(f"{prefix}%"),
        )
        .count()
    )
    return f"{prefix}{count + 1:04d}"

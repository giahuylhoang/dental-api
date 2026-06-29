"""Schema-level checks for the CRM patient-attach migration."""
from sqlalchemy import inspect

from database.clinical.models import PatientNote, Document


def test_patient_note_model_columns():
    cols = {c.name for c in PatientNote.__table__.columns}
    assert cols == {
        "id", "clinic_id", "patient_id", "author_id",
        "body", "created_at", "updated_at",
    }
    assert PatientNote.__tablename__ == "patient_notes"


def test_document_has_new_columns():
    cols = {c.name for c in Document.__table__.columns}
    assert "storage_backend" in cols
    assert "original_name" in cols


def test_document_unique_constraint_is_patient_scoped():
    uniques = [
        tuple(col.name for col in c.columns)
        for c in Document.__table__.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    ]
    assert ("clinic_id", "patient_id", "content_sha256") in uniques
    assert ("clinic_id", "content_sha256") not in uniques


def test_patient_notes_table_created_on_sqlite(db_engine):
    # db_engine fixture builds all tables on in-memory SQLite
    names = inspect(db_engine).get_table_names()
    assert "patient_notes" in names

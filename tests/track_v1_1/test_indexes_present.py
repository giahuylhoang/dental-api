"""Smoke-check that the v1.1 performance indexes exist on a freshly-built DB."""
from sqlalchemy import inspect


REQUIRED_INDEXES = {
    "patients": {"ix_patients_clinic"},
    "appointments": {
        "ix_appointments_clinic_start",
        "ix_appointments_clinic_status",
        "ix_appointments_patient_start",
    },
    "leads": {"ix_leads_clinic_status"},
    "invoices": {"ix_invoices_clinic_status"},
    "insurance_claims": {"ix_claims_clinic_status"},
    "appointment_reminders": {"ix_appt_reminders_status_due"},
    "recalls": {"ix_recalls_clinic_due_status", "ix_recalls_patient_status",
                "ux_recalls_active_patient_rule"},
    "lab_cases": {"ix_lab_cases_clinic_status"},
    "denture_cases": {"ix_denture_cases_patient_status"},
    "communications": {"ix_communications_patient_created"},
    "audit_log": {"ix_audit_log_entity"},
    "clinical_notes": {"ix_clinical_notes_patient_created"},
}


def test_required_indexes_exist(db_engine):
    insp = inspect(db_engine)
    for table, expected in REQUIRED_INDEXES.items():
        actual = {idx["name"] for idx in insp.get_indexes(table)}
        missing = expected - actual
        assert not missing, f"Missing indexes on {table}: {missing}. Got {actual}"

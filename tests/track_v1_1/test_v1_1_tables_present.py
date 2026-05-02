"""All v1.1 sibling tables exist after create_all / migration."""
from sqlalchemy import inspect


V1_1_TABLES = [
    "patient_communication_preferences",
    "clinic_operating_hours",
    "clinic_closures",
    "provider_time_off",
    "tooth_chart_entries",
    "denture_case_implants",
    "patient_relationships",
    "clinic_sequences",
    "human_identifiers",
    "provider_compensation_history",
    "inventory_items",
    "inventory_lots",
    "lab_case_materials",
    "claim_response_codes",
]


def test_v1_1_tables_exist(db_engine):
    insp = inspect(db_engine)
    tables = set(insp.get_table_names())
    missing = [t for t in V1_1_TABLES if t not in tables]
    assert not missing, f"Missing v1.1 tables: {missing}"

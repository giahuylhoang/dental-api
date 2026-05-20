"""track2_clinical

Revision ID: a1b2c3d4e5f6
Revises: 653b32d48895
Create Date: 2026-05-02 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '653b32d48895'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('patient_medical_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('bisphosphonates_use', sa.Boolean(), nullable=True),
        sa.Column('allergies_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('patient_allergies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('reaction', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('patient_medications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('dose', sa.String(), nullable=True),
        sa.Column('since', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('patient_insurance',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('carrier', sa.String(), nullable=False),
        sa.Column('policy_number', sa.String(), nullable=True),
        sa.Column('group_number', sa.String(), nullable=True),
        sa.Column('holder_name', sa.String(), nullable=True),
        sa.Column('holder_relationship', sa.String(), nullable=True),
        sa.Column('assignment_of_benefits', sa.Boolean(), nullable=True),
        sa.Column('coverage_pct_by_category', sa.JSON(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('patient_consent',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('form_kind', sa.String(), nullable=False),
        sa.Column('form_version', sa.String(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('signature_blob_url', sa.Text(), nullable=True),
        sa.Column('witness_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('storage_url', sa.Text(), nullable=False),
        sa.Column('content_sha256', sa.String(), nullable=False),
        sa.Column('mime', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clinic_id', 'content_sha256', name='uq_doc_clinic_sha'),
    )
    op.create_table('clinical_notes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('soap_subjective', sa.Text(), nullable=True),
        sa.Column('soap_objective', sa.Text(), nullable=True),
        sa.Column('soap_assessment', sa.Text(), nullable=True),
        sa.Column('soap_plan', sa.Text(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('supersedes_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['supersedes_id'], ['clinical_notes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('denture_cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('arch', sa.String(), nullable=False),
        sa.Column('case_type', sa.String(), nullable=False),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('denture_case_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('provider_id', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('photo_document_ids', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['denture_cases.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('procedures',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('default_duration_min', sa.Integer(), nullable=True),
        sa.Column('default_fee', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clinic_id', 'code', name='uq_procedure_clinic_code'),
    )
    op.create_table('treatment_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('total_estimate', sa.Float(), nullable=True),
        sa.Column('insurance_estimate', sa.Float(), nullable=True),
        sa.Column('patient_estimate', sa.Float(), nullable=True),
        sa.Column('presented_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('declined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('treatment_plan_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=True),
        sa.Column('procedure_code', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fee', sa.Float(), nullable=True),
        sa.Column('insurance_coverage_pct', sa.Float(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['treatment_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('lab_vendors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('sla_days', sa.Integer(), nullable=True),
        sa.Column('price_list', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('lab_cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('denture_case_id', sa.String(), nullable=False),
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('due_back_at', sa.DateTime(), nullable=True),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('remake_of_id', sa.String(), nullable=True),
        sa.Column('remake_reason', sa.Text(), nullable=True),
        sa.Column('lab_fee', sa.Float(), nullable=True),
        sa.Column('courier_tracking', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['denture_case_id'], ['denture_cases.id']),
        sa.ForeignKeyConstraint(['vendor_id'], ['lab_vendors.id']),
        sa.ForeignKeyConstraint(['remake_of_id'], ['lab_cases.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('lab_case_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lab_case_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['lab_case_id'], ['lab_cases.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('lab_case_events')
    op.drop_table('lab_cases')
    op.drop_table('lab_vendors')
    op.drop_table('treatment_plan_items')
    op.drop_table('treatment_plans')
    op.drop_table('procedures')
    op.drop_table('denture_case_events')
    op.drop_table('denture_cases')
    op.drop_table('clinical_notes')
    op.drop_table('documents')
    op.drop_table('patient_consent')
    op.drop_table('patient_insurance')
    op.drop_table('patient_medications')
    op.drop_table('patient_allergies')
    op.drop_table('patient_medical_history')

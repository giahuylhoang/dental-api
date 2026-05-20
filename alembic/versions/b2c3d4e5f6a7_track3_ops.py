"""track3_ops

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('operatories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('equipment_tags', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('appointment_resources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('operatory_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['operatory_id'], ['operatories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('appointment_recurrences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('parent_appointment_id', sa.String(), nullable=False),
        sa.Column('rule', sa.Text(), nullable=False),
        sa.Column('generated_through_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['parent_appointment_id'], ['appointments.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('appointment_reminders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('offset_minutes', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('waitlist_entries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('requested_window_start', sa.DateTime(), nullable=False),
        sa.Column('requested_window_end', sa.DateTime(), nullable=False),
        sa.Column('provider_pref', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['provider_pref'], ['providers.id']),
        sa.ForeignKeyConstraint(['service_id'], ['services.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('recall_rules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('trigger_event', sa.String(), nullable=False),
        sa.Column('offset_days', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('recalls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('due_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['rule_id'], ['recall_rules.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('invoices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('treatment_plan_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('subtotal', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('gst', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('total', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('balance', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('invoice_lines',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('invoice_id', sa.String(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=True),
        sa.Column('procedure_code', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('qty', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('total', sa.DECIMAL(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('payments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('invoice_id', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('insurance_claims',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('invoice_id', sa.String(), nullable=True),
        sa.Column('carrier', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('assignment_of_benefits', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('adjudicated_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('claim_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('claim_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['insurance_claims.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('communications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('related_appointment_id', sa.String(), nullable=True),
        sa.Column('related_invoice_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['related_appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['related_invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('marketing_campaigns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('clinic_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('audience_query', sa.JSON(), nullable=True),
        sa.Column('schedule_at', sa.DateTime(), nullable=True),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('lead_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lead_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('lead_events')
    op.drop_table('marketing_campaigns')
    op.drop_table('communications')
    op.drop_table('claim_events')
    op.drop_table('insurance_claims')
    op.drop_table('payments')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('recalls')
    op.drop_table('recall_rules')
    op.drop_table('waitlist_entries')
    op.drop_table('appointment_reminders')
    op.drop_table('appointment_recurrences')
    op.drop_table('appointment_resources')
    op.drop_table('operatories')

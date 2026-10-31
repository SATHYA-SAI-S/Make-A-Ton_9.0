"""revenue guardian tables

Revision ID: p3_0006
Revises: p3_0005
Create Date: 2026-10-31 15:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_0006'
down_revision: Union[str, None] = 'p3_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. risk_alerts table
    op.create_table(
        'risk_alerts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('rule_key', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('payment_id', sa.String(length=36), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('estimated_impact', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('suggested_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('acknowledged_by', sa.String(length=100), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('fingerprint', sa.String(length=255), nullable=False, unique=True),
    )
    op.create_index('ix_risk_alerts_status_severity', 'risk_alerts', ['status', 'severity'])
    op.create_index('ix_risk_alerts_customer_id', 'risk_alerts', ['customer_id'])
    op.create_index('ix_risk_alerts_detected_at', 'risk_alerts', ['detected_at'])

    # 2. risk_detection_runs table
    op.create_table(
        'risk_detection_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rules_run', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('alerts_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='RUNNING'),
        sa.Column('error', sa.Text(), nullable=True),
    )
    op.create_index('ix_risk_detection_runs_started_at', 'risk_detection_runs', ['started_at'])


def downgrade() -> None:
    op.drop_index('ix_risk_detection_runs_started_at', table_name='risk_detection_runs')
    op.drop_table('risk_detection_runs')
    op.drop_index('ix_risk_alerts_detected_at', table_name='risk_alerts')
    op.drop_index('ix_risk_alerts_customer_id', table_name='risk_alerts')
    op.drop_index('ix_risk_alerts_status_severity', table_name='risk_alerts')
    op.drop_table('risk_alerts')

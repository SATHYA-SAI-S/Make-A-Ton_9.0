"""customer requests

Revision ID: p3_0002
Revises: p3_0001
Create Date: 2026-10-31 13:05:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_0002'
down_revision: Union[str, None] = 'p3_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'customer_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('subscription_id', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('target_plan_id', sa.String(length=100), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('decided_by', sa.String(length=100), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_custreq_customer_status', 'customer_requests', ['customer_id', 'status'])
    op.create_index('ix_custreq_subscription', 'customer_requests', ['subscription_id'])

def downgrade() -> None:
    op.drop_index('ix_custreq_subscription', table_name='customer_requests')
    op.drop_index('ix_custreq_customer_status', table_name='customer_requests')
    op.drop_table('customer_requests')

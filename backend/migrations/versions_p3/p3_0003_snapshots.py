"""revenue and analytics snapshots

Revision ID: p3_0003
Revises: p3_0002
Create Date: 2026-10-31 13:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_0003'
down_revision: Union[str, None] = 'p3_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. revenue_snapshots table
    op.create_table(
        'revenue_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('mrr', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('arr', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('invoiced', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('collected', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('outstanding', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('active_subscriptions', sa.Integer(), nullable=False),
        sa.Column('customers', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period', name='uq_revenue_snapshots_period')
    )
    op.create_index('ix_revenue_snapshots_period', 'revenue_snapshots', ['period'])

    # 2. analytics_snapshots table
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('metric_key', sa.String(length=100), nullable=False),
        sa.Column('dimension', sa.String(length=100), nullable=True),
        sa.Column('period', sa.String(length=50), nullable=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_snapshots_key', 'analytics_snapshots', ['metric_key'])
    op.create_index('ix_analytics_snapshots_lookup', 'analytics_snapshots', ['metric_key', 'dimension', 'period'])

def downgrade() -> None:
    op.drop_index('ix_analytics_snapshots_lookup', table_name='analytics_snapshots')
    op.drop_index('ix_analytics_snapshots_key', table_name='analytics_snapshots')
    op.drop_table('analytics_snapshots')

    op.drop_index('ix_revenue_snapshots_period', table_name='revenue_snapshots')
    op.drop_table('revenue_snapshots')

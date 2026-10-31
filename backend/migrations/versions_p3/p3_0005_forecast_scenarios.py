"""forecast scenarios table

Revision ID: p3_0005
Revises: p3_0004
Create Date: 2026-10-31 14:40:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_0005'
down_revision: Union[str, None] = 'p3_0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'forecast_scenarios',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('horizon_months', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('assumptions', sa.JSON(), nullable=False),
        sa.Column('projection', sa.JSON(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_forecast_scenarios_created_at', 'forecast_scenarios', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_forecast_scenarios_created_at', table_name='forecast_scenarios')
    op.drop_table('forecast_scenarios')

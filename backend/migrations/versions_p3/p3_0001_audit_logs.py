"""audit logs

Revision ID: p3_0001
Revises: base
Create Date: 2026-10-31 12:55:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p3_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = 'p3'
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('actor_role', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_actor_time', 'audit_logs', ['actor_id', 'occurred_at'])
    op.create_index('ix_audit_action_time', 'audit_logs', ['action', 'occurred_at'])

def downgrade() -> None:
    op.drop_index('ix_audit_action_time', table_name='audit_logs')
    op.drop_index('ix_audit_actor_time', table_name='audit_logs')
    op.drop_index('ix_audit_entity', table_name='audit_logs')
    op.drop_table('audit_logs')

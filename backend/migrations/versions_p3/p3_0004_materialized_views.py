"""materialized views for revenue aggregates

Revision ID: p3_0004
Revises: p3_0003
Create Date: 2026-10-31 13:31:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_0004'
down_revision: Union[str, None] = 'p3_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Create true PostgreSQL Materialized View for heavy monthly invoice aggregates
        op.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_monthly_summary AS
            SELECT 
                TO_CHAR(invoice_date, 'YYYY-MM') AS month_key,
                COUNT(id) AS total_invoices,
                COALESCE(SUM(total), 0) AS total_invoiced,
                COALESCE(SUM(amount_paid), 0) AS total_collected,
                COALESCE(SUM(balance), 0) AS total_outstanding
            FROM invoices
            WHERE status != 'CANCELLED'
            GROUP BY TO_CHAR(invoice_date, 'YYYY-MM')
        """)
        op.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_revenue_month_key 
            ON mv_revenue_monthly_summary (month_key)
        """)
    else:
        # SQLite / generic compatible view
        op.execute("""
            CREATE VIEW IF NOT EXISTS mv_revenue_monthly_summary AS
            SELECT 
                SUBSTR(invoice_date, 1, 7) AS month_key,
                COUNT(id) AS total_invoices,
                COALESCE(SUM(total), 0) AS total_invoiced,
                COALESCE(SUM(amount_paid), 0) AS total_collected,
                COALESCE(SUM(balance), 0) AS total_outstanding
            FROM invoices
            WHERE status != 'CANCELLED'
            GROUP BY SUBSTR(invoice_date, 1, 7)
        """)

def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_revenue_monthly_summary")
    else:
        op.execute("DROP VIEW IF EXISTS mv_revenue_monthly_summary")

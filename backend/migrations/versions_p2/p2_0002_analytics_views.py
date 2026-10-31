"""read-optimized analytics and finance views for Person 3

Revision ID: p2_0002
Revises: p2_0001
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'p2_0002'
down_revision = 'p2_0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Invoice Summary View (Aggregated invoice header and line items count)
    op.execute("""
    CREATE VIEW IF NOT EXISTS v_invoice_summary AS
    SELECT
        i.id AS invoice_id,
        i.number AS invoice_number,
        i.customer_id,
        i.subscription_id,
        i.status,
        i.invoice_date,
        i.due_date,
        i.currency,
        i.subtotal,
        i.discount_total,
        i.tax_total,
        i.total,
        i.amount_paid,
        i.balance,
        COUNT(il.id) AS line_item_count,
        CASE
            WHEN i.status IN ('CONFIRMED', 'PARTIALLY_PAID') AND i.balance > 0 AND i.due_date < CURRENT_DATE
            THEN 1 ELSE 0
        END AS is_overdue,
        i.created_at,
        i.updated_at
    FROM invoices i
    LEFT JOIN invoice_lines il ON il.invoice_id = i.id
    GROUP BY
        i.id, i.number, i.customer_id, i.subscription_id, i.status,
        i.invoice_date, i.due_date, i.currency, i.subtotal, i.discount_total,
        i.tax_total, i.total, i.amount_paid, i.balance, i.created_at, i.updated_at;
    """)

    # 2. Payment Summary View (Aggregated payment allocations and refunds)
    op.execute("""
    CREATE VIEW IF NOT EXISTS v_payment_summary AS
    SELECT
        p.id AS payment_id,
        p.customer_id,
        p.method,
        p.amount,
        COALESCE(SUM(pa.amount), 0.00) AS total_allocated,
        p.unallocated_amount,
        COALESCE(pr.total_refunded, 0.00) AS total_refunded,
        p.reference,
        p.status,
        p.payment_date,
        p.created_at
    FROM payments p
    LEFT JOIN payment_allocations pa ON pa.payment_id = p.id
    LEFT JOIN (
        SELECT payment_id, SUM(amount) AS total_refunded
        FROM payment_refunds
        GROUP BY payment_id
    ) pr ON pr.payment_id = p.id
    GROUP BY
        p.id, p.customer_id, p.method, p.amount,
        p.unallocated_amount, pr.total_refunded, p.reference,
        p.status, p.payment_date, p.created_at;
    """)

    # 3. Outstanding Customer Balances View (Pre-calculated net debt)
    op.execute("""
    CREATE VIEW IF NOT EXISTS v_outstanding AS
    SELECT
        c_inv.customer_id,
        COALESCE(c_inv.total_invoiced, 0.00) AS total_invoiced,
        COALESCE(c_inv.total_paid, 0.00) AS total_paid,
        COALESCE(c_inv.total_outstanding_balance, 0.00) AS total_outstanding_balance,
        COALESCE(c_pay.unallocated_credits, 0.00) AS unallocated_credits,
        CASE
            WHEN COALESCE(c_inv.total_outstanding_balance, 0.00) - COALESCE(c_pay.unallocated_credits, 0.00) > 0
            THEN COALESCE(c_inv.total_outstanding_balance, 0.00) - COALESCE(c_pay.unallocated_credits, 0.00)
            ELSE 0.00
        END AS net_due
    FROM (
        SELECT
            customer_id,
            SUM(total) AS total_invoiced,
            SUM(amount_paid) AS total_paid,
            SUM(CASE WHEN status IN ('CONFIRMED', 'PARTIALLY_PAID') THEN balance ELSE 0.00 END) AS total_outstanding_balance
        FROM invoices
        WHERE status != 'CANCELLED'
        GROUP BY customer_id
    ) c_inv
    LEFT JOIN (
        SELECT
            customer_id,
            SUM(unallocated_amount) AS unallocated_credits
        FROM payments
        WHERE status = 'RECORDED'
        GROUP BY customer_id
    ) c_pay ON c_pay.customer_id = c_inv.customer_id;
    """)

def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_outstanding;")
    op.execute("DROP VIEW IF EXISTS v_payment_summary;")
    op.execute("DROP VIEW IF EXISTS v_invoice_summary;")

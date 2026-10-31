"""tax, discounts, billing, invoices and payments tables

Revision ID: p2_0001
Revises: None
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = 'p2_0001'
down_revision = None
branch_labels = ('p2',)
depends_on = None

def upgrade() -> None:
    # Tax tables
    op.create_table(
        'tax_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rate', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tax_rule_products',
        sa.Column('rule_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['tax_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rule_id', 'product_id')
    )

    op.create_table(
        'tax_calculation_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_line_id', sa.String(length=36), nullable=True),
        sa.Column('rule_id', sa.String(length=36), nullable=True),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rate', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('base_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'billing_settings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('company_state_code', sa.String(length=10), nullable=False),
        sa.Column('company_gstin', sa.String(length=30), nullable=False),
        sa.Column('default_currency', sa.String(length=10), nullable=False),
        sa.Column('invoice_prefix', sa.String(length=20), nullable=False),
        sa.Column('invoice_sequence', sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Discount tables
    op.create_table(
        'discount_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('min_purchase', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('max_usage', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, default=0),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=1),
        sa.Column('stackable', sa.Boolean(), nullable=False, default=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'discount_redemptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rule_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['discount_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Billing and invoice tables
    op.create_table(
        'billing_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('triggered_by', sa.String(length=50), nullable=False),
        sa.Column('subscriptions_checked', sa.Integer(), nullable=False, default=0),
        sa.Column('invoices_created', sa.Integer(), nullable=False, default=0),
        sa.Column('failures', sa.Integer(), nullable=False, default=0),
        sa.Column('error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'billing_run_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['billing_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'billing_periods',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subscription_id', 'period_start', 'period_end', name='uq_subscription_billing_period')
    )

    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('billing_period_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('discount_total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('tax_total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('amount_paid', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('balance', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number'),
        sa.UniqueConstraint('billing_period_id')
    )
    op.create_index('idx_invoices_customer_status', 'invoices', ['customer_id', 'status'])
    op.create_index('idx_invoices_due_date', 'invoices', ['due_date'])
    op.create_index('idx_invoices_subscription_id', 'invoices', ['subscription_id'])

    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('variant_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Payments and allocations
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('method', sa.String(length=30), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('unallocated_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('gateway_event_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gateway_event_id')
    )
    op.create_index('idx_payments_customer_id', 'payments', ['customer_id'])

    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payment_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_payment_allocations_invoice_id', 'payment_allocations', ['invoice_id'])

def downgrade() -> None:
    op.drop_table('payment_allocations')
    op.drop_table('payments')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('billing_periods')
    op.drop_table('billing_run_items')
    op.drop_table('billing_runs')
    op.drop_table('discount_redemptions')
    op.drop_table('discount_rules')
    op.drop_table('billing_settings')
    op.drop_table('tax_calculation_history')
    op.drop_table('tax_rule_products')
    op.drop_table('tax_rules')

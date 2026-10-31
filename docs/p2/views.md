# Read-Optimized SQL Views for Analytics & Finance (Person 3)

This document defines the 3 read-optimized database views provided by Person 2 (Billing Engine) for Person 3 (Finance, Audit, Portal & Analytics personas).

These views eliminate complex multi-table joins across `invoices`, `invoice_lines`, `payments`, `payment_allocations`, and `payment_refunds`, allowing high-performance analytical queries and portal dashboards.

---

## 1. `v_invoice_summary`

### Purpose
Provides a consolidated header-level view of all invoices with pre-aggregated line item counts, dynamic overdue flag (`is_overdue`), and complete monetary totals in pure `Decimal(14, 2)`.

### Schema Definition
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `invoice_id` | `VARCHAR(36)` | Primary UUID of the invoice |
| `invoice_number` | `VARCHAR(50)` | Sequential human-readable identifier (e.g. `INV-2026-000001`) |
| `customer_id` | `VARCHAR(36)` | Customer UUID |
| `subscription_id` | `VARCHAR(36)` | Originating subscription UUID (nullable for one-off invoices) |
| `status` | `VARCHAR(20)` | Lifecycle state: `DRAFT`, `CONFIRMED`, `PARTIALLY_PAID`, `PAID`, `CANCELLED` |
| `invoice_date` | `DATE` | Billing date of issuance |
| `due_date` | `DATE` | Payment due date (default: issuance + payment terms) |
| `currency` | `VARCHAR(10)` | ISO currency (e.g. `INR`) |
| `subtotal` | `NUMERIC(14, 2)` | Net sum of line item base prices before discounts/tax |
| `discount_total` | `NUMERIC(14, 2)` | Total discounts deducted |
| `tax_total` | `NUMERIC(14, 2)` | Total place-of-supply GST applied |
| `total` | `NUMERIC(14, 2)` | Final payable invoice total |
| `amount_paid` | `NUMERIC(14, 2)` | Cumulative amount paid via allocations |
| `balance` | `NUMERIC(14, 2)` | Remaining unpaid balance (`total - amount_paid`) |
| `line_item_count` | `INTEGER` | Total number of itemized lines on the invoice |
| `is_overdue` | `INTEGER` (0 or 1) | `1` if status is `CONFIRMED`/`PARTIALLY_PAID`, `balance > 0`, and `due_date < CURRENT_DATE` |
| `created_at` | `TIMESTAMPTZ` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Record modification timestamp |

### Example Query
```sql
-- Find top 10 overdue invoices by balance
SELECT
    invoice_number,
    customer_id,
    due_date,
    total,
    balance
FROM v_invoice_summary
WHERE is_overdue = 1
ORDER BY balance DESC
LIMIT 10;
```

---

## 2. `v_payment_summary`

### Purpose
Aggregates all customer transactions, total applied invoice allocations, surplus advance credit, and issued refunds.

### Schema Definition
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `payment_id` | `VARCHAR(36)` | Primary UUID of the payment |
| `customer_id` | `VARCHAR(36)` | Customer UUID |
| `method` | `VARCHAR(30)` | Payment method: `UPI`, `CARD`, `BANK_TRANSFER`, `CASH`, `OTHER` |
| `amount` | `NUMERIC(14, 2)` | Captured transaction amount |
| `total_allocated` | `NUMERIC(14, 2)` | Cumulative amount allocated across invoices |
| `unallocated_amount` | `NUMERIC(14, 2)` | Remaining advance credit available for allocation |
| `total_refunded` | `NUMERIC(14, 2)` | Cumulative amount refunded from this payment |
| `reference` | `VARCHAR(100)` | External payment gateway transaction reference / UTR |
| `status` | `VARCHAR(20)` | `RECORDED`, `FAILED`, `REFUNDED` |
| `payment_date` | `TIMESTAMPTZ` | Date and time payment was recorded |
| `created_at` | `TIMESTAMPTZ` | System insertion timestamp |

### Example Query
```sql
-- Total payment volume and breakdown by payment method for the current month
SELECT
    method,
    COUNT(*) AS transaction_count,
    SUM(amount) AS gross_captured,
    SUM(unallocated_amount) AS total_unallocated_credit,
    SUM(total_refunded) AS total_refunds
FROM v_payment_summary
WHERE status = 'RECORDED'
GROUP BY method
ORDER BY gross_captured DESC;
```

---

## 3. `v_outstanding`

### Purpose
Provides a real-time ledger balance per customer, factoring in total invoiced, total paid, gross unpaid invoice balances, unallocated customer advance credits, and the true net debt (`net_due`).

### Schema Definition
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `customer_id` | `VARCHAR(36)` | Customer UUID |
| `total_invoiced` | `NUMERIC(14, 2)` | Cumulative non-cancelled invoice volume |
| `total_paid` | `NUMERIC(14, 2)` | Cumulative payments allocated |
| `total_outstanding_balance` | `NUMERIC(14, 2)` | Gross remaining balance on open invoices |
| `unallocated_credits` | `NUMERIC(14, 2)` | Total unallocated advance payments on account |
| `net_due` | `NUMERIC(14, 2)` | Real net debt: `MAX(0, total_outstanding_balance - unallocated_credits)` |

### Example Query
```sql
-- Customers with actionable net debt for collection follow-ups
SELECT
    customer_id,
    total_outstanding_balance,
    unallocated_credits,
    net_due
FROM v_outstanding
WHERE net_due > 0.00
ORDER BY net_due DESC;
```

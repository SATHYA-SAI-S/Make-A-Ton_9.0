# SubscriptIQ: Person 2 (Billing Engine) Specification

## 1. Scope & Objective
SubscriptIQ is the subscription management and recurring billing platform for Brightloop Software.
Person 2 owns the **Billing, Invoicing and Payment Engine**: everything that calculates, moves, records, and reconciles money.

### Core Responsibilities:
1. **Notifications Service (`NotificationPort`)**: Jinja2 templated transactional emails for billing, invoicing, payments, and system notices.
2. **Tax Management (`taxes/`)**: Place-of-supply rules (Intra-state CGST + SGST vs Inter-state IGST), tax calculation history, pure `compute_tax`, and `TaxPreviewPort`.
3. **Discount Management (`discounts/`)**: Fixed and percentage discount rules, scope (product/subscription), eligibility rules, usage tracking with concurrency safety (`SELECT FOR UPDATE`), discount performance report.
4. **Pricing Calculator (`billing/calculator.py`)**: Pure logic calculator in Python `Decimal` (`ROUND_HALF_UP`) with zero floating-point arithmetic.
5. **Billing Engine (`billing/engine.py`)**: Idempotent billing execution, PostgreSQL advisory locking, period generation, line price snapshot application, missed runs catch-up, and `SubscriptionPort.set_next_billing_date`.
6. **Invoicing Lifecycle (`invoices/`)**: Numbering sequence `INV-YYYY-000001`, lifecycle states (`DRAFT` -> `CONFIRMED` -> `PARTIALLY_PAID` -> `PAID` / `CANCELLED`), immutable JSON snapshot, PDF rendering & dispatch, and `InvoicePort`.
7. **Payments & Allocation (`payments/`, `allocations/`)**: Multiple payment methods (UPI, Card, Bank Transfer, Cash, Other), split payment allocations, balance reconciliation, refunds, and `PaymentPort`.
8. **Payment Gateway Integration (`payments/gateway.py`)**: Test-mode Razorpay / Stripe order creation, webhook verification with idempotency keys.
9. **Overdue & Reminders (`overdue/`)**: Dynamic `is_overdue` derivation, multi-tier escalation policies, reminder tracking.
10. **Reconciliation Service (`reconciliation/`)**: Comprehensive audit detecting payment allocation mismatches, dangling balances, and orphaned credits.
11. **Frontend Module (`frontend/src/modules/p2/`)**: React + TypeScript user interface for taxes, discounts, billing control, invoices, payments, overdue tracking, and reconciliation.
12. **Read-Optimized Views (`docs/p2/views.md`)**: `v_invoice_summary`, `v_payment_summary`, `v_outstanding`.

---

## 2. Invariant Rules & Contracts
1. **Zero Floats**: All currency values must use Python `Decimal` with banker-safe rounding (`ROUND_HALF_UP`) and serialized as strings (e.g. `"1250.00"`) in JSON APIs.
2. **No Cross-Domain Table Writes**: Person 2 reads Person 1 tables (`customers`, `subscriptions`, `products`, `plans`), but **never writes** to them. The sole exception is updating the subscription billing pointer via `SubscriptionPort.set_next_billing_date`.
3. **Idempotent Billing**: Running the billing engine multiple times for the same date/period must yield exactly one invoice per subscription per period. Enforced via database constraint `UNIQUE(subscription_id, period_start, period_end)` on `billing_periods` and advisory locks.
4. **Immutable Invoice Snapshots**: Once an invoice is generated/confirmed, it retains an immutable snapshot of customer info, plan terms, item prices, and tax rates. Subsequent changes to product catalog or tax rules never alter existing invoices.
5. **Payment Allocation Integrity**: Allocations across invoices cannot exceed the total payment amount or the remaining balance of any target invoice.

---

## 3. State Machines

### 3.1 Invoice State Machine
- `DRAFT`: Initial draft created by billing run or manual draft.
- `CONFIRMED`: Official invoice ready for payment, taxes finalized.
- `PARTIALLY_PAID`: `0 < amount_paid < total`.
- `PAID`: `amount_paid == total` and `balance == 0`.
- `CANCELLED`: Terminal state, only permitted from `DRAFT` or `CONFIRMED` when `amount_paid == 0`. Requires cancellation reason.
- Derived property: `is_overdue = (status in [CONFIRMED, PARTIALLY_PAID] and balance > 0 and due_date < today)`.

### 3.2 Billing Period Status
- `PENDING`: Period identified.
- `BILLED`: Invoice generated.
- `SKIPPED`: Period skipped (e.g. paused subscription).

### 3.3 Payment Status
- `RECORDED`: Payment registered and allocated.
- `FAILED`: Payment failure logged.
- `REFUNDED`: Payment refunded / balance restored.

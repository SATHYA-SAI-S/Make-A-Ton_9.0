# SubscriptIQ: Person 2 Roadmap

## Phase 1: Foundation & Shared Scaffolding
- [x] Establish directory structure, core models, Money type, shared ports, DTOs, events, fakes, and registry
- [x] Configure scripts (save.sh, sync.sh, check_ownership.py) and setup docs contracts
- [x] Automated tests: test_foundation.py

## Phase 2: Notification Service (P2-T01)
- [x] NotificationPort implementation with bootstrap registration
- [x] Jinja2 transactional templates (password_reset, invoice_generated, invoice_confirmed, due_reminder, overdue_reminders, payment_received, payment_failed, renewal_confirmed)
- [x] Notifications data model and query endpoint GET /api/v1/notifications
- [x] Automated tests: test_notifications.py

## Phase 3: Tax Rules & Place-of-Supply Engine (P2-T02)
- [x] Tax rules models (tax_rules, tax_rule_products) and calculation history
- [x] Place-of-supply logic (Intra-state CGST + SGST vs Inter-state IGST)
- [x] Pure function compute_tax and TaxPreviewPort.preview registration
- [x] Automated tests: test_taxes.py

## Phase 4: Discount Rules & Eligibility (P2-T03)
- [x] Discount rules and redemptions models
- [x] Concurrency-safe eligibility service with row locking (SELECT ... FOR UPDATE)
- [x] Discount performance reporting endpoint GET /api/v1/discounts/performance
- [x] Automated tests: test_discounts.py

## Phase 5: Pricing Calculator (P2-T04)
- [x] Pure logic Decimal pricing calculator in billing/calculator.py
- [x] Strict calculation order and zero-float enforcement
- [x] Documentation docs/p2/calculation.md
- [x] Automated tests: test_calculator.py

## Phase 6: Billing & Invoice Database Models & Migration (P2-T05)
- [ ] Billing models: billing_runs, billing_run_items, billing_periods, invoices, invoice_lines, payments, payment_allocations, billing_settings
- [ ] Unique constraints and optimized indexing for analytics
- [ ] Alembic migration p2_0001
- [ ] Automated tests: test_models_migrations.py

## Phase 7: Invoice Lifecycle, Snapshots & PDF Generation (P2-T06, P2-T09)
- [ ] State machine transitions (DRAFT -> CONFIRMED -> PARTIALLY_PAID -> PAID, CANCELLED)
- [ ] Immutable snapshot JSON storage
- [ ] PDF rendering and InvoicePort (list_for_customer, get, pdf)
- [ ] Automated tests: test_invoices.py

## Phase 8: Billing Engine with Idempotency & Locking (P2-T07, P2-T08)
- [ ] Advisory locked billing engine in billing/engine.py
- [ ] Period calculation across frequencies and missed periods detector
- [ ] Idempotent period insertion and SubscriptionPort.set_next_billing_date invocation
- [ ] Billing scheduler, retries with exponential backoff, and dry-run support
- [ ] Automated tests: test_billing_engine.py

## Phase 9: Payments, Split Allocation & Refunds (P2-T10, P2-T11)
- [ ] Payment recording across methods (UPI, Card, Bank Transfer, Cash, Other)
- [ ] Split allocation engine (1-to-many, many-to-1) with balance controls
- [ ] Refunds and failed payment logging
- [ ] Payment gateway test-mode order and webhook handler with signature checks
- [ ] PaymentPort registration
- [ ] Automated tests: test_payments.py

## Phase 10: Overdue Management, Reminders & Reconciliation (P2-T12, P2-T13)
- [ ] Overdue detection and escalation tiers (1, 2, 3)
- [ ] Follow-up history and collection summary endpoints
- [ ] Comprehensive reconciliation service comparing payments, allocations, and invoices
- [ ] Automated tests: test_overdue_reconciliation.py

## Phase 11: Frontend Module (P2-T14)
- [ ] React + TypeScript views: Taxes, Discounts, Billing Control, Invoices, Payments, Overdue, Reconciliation
- [ ] Component tests with Vitest and E2E Playwright tests in e2e/p2/

## Phase 12: Views, Hardening & Final Documentation (P2-T15)
- [ ] Read-optimized SQL views: v_invoice_summary, v_payment_summary, v_outstanding
- [ ] Documentation docs/p2/api.md and docs/p2/views.md
- [ ] Codebase audit: zero float check, secret leak check, error consistency

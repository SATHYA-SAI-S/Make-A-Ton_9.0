# SubscriptIQ: Architecture Document

## 1. Monorepo Structure
SubscriptIQ is architected as an event-driven, modular monorepo cleanly separated across three persona boundaries:

```
subscriptiq/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, DB engine, Base model, Money type, security dependencies
│   │   ├── shared/            # Hexagonal Ports, Events, DTOs, In-memory Fakes, Registry
│   │   ├── main.py            # FastAPI application with dynamic router auto-discovery
│   │   ├── celery_app.py      # Celery task and beat schedule auto-discovery
│   │   ├── taxes/             # Person 2: Tax rules, Place-of-Supply, TaxPreviewPort
│   │   ├── discounts/         # Person 2: Discount rules, Eligibility engine
│   │   ├── billing/           # Person 2: Pricing calculator, Billing engine, Scheduler, ControlPort
│   │   ├── invoices/          # Person 2: Invoice lifecycle, Snapshots, PDF generation, InvoicePort
│   │   ├── payments/          # Person 2: Payments, PaymentPort, Gateway integration
│   │   ├── allocations/       # Person 2: Split payment allocations, balance tracking
│   │   ├── reconciliation/    # Person 2: Audit & reconciliation reporting
│   │   ├── notifications/     # Person 2: Transactional templates & NotificationPort
│   │   ├── overdue/           # Person 2: Escalations, reminders & followups
│   │   └── ...                # Other persona modules (auth, customers, portal, etc.)
│   ├── migrations/
│   │   ├── versions_p1/
│   │   ├── versions_p2/       # Person 2 Alembic migrations (p2_0001...)
│   │   └── versions_p3/
│   ├── tests/
│   │   ├── conftest.py
│   │   └── p2/                # Person 2 comprehensive test suite
│   └── requirements/
│       ├── base.txt
│       └── p2.txt
├── frontend/
│   └── src/
│       ├── app/               # Layout, router & shell
│       ├── shared/            # Shared UI design system, api client, auth store
│       └── modules/
│           └── p2/            # Person 2 UI (Billing, Invoices, Taxes, Discounts, Payments, Overdue)
├── e2e/
│   └── p2/                    # Playwright test suite
├── docs/
│   ├── contracts/             # Shared schema and API contracts
│   └── p2/                    # Person 2 technical documentation & views
└── scripts/
    ├── save.sh                # Commit & push helper with ownership validation
    ├── sync.sh                # Merge develop helper
    └── check_ownership.py     # Code boundary enforcer
```

## 2. Ports & Fakes Architecture (Hexagonal Architecture)
Modules communicate through interfaces defined in `backend/app/shared/ports.py`:
- `NotificationPort` (Implemented by Person 2)
- `TaxPreviewPort` (Implemented by Person 2)
- `InvoicePort` (Implemented by Person 2)
- `PaymentPort` (Implemented by Person 2)
- `BillingControlPort` (Implemented by Person 2)
- `SubscriptionPort` (Implemented by Person 1; faked in `shared/fakes.py` until merged)
- `CustomerPort` (Implemented by Person 1; faked in `shared/fakes.py` until merged)
- `AuditPort` (Implemented by Person 3; faked in `shared/fakes.py` until merged)

This decouples development and guarantees that no team member is ever blocked on unfinished dependencies.

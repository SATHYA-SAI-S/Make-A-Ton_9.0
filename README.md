# SubscriptIQ — Subscription Management System (Person 1: Core Management)

SubscriptIQ is a unified subscription-to-cash platform built with a FastAPI modular monolith backend, React + TypeScript + Tailwind CSS frontend, and dual SQLite / PostgreSQL database support via SQLAlchemy 2.0.

This repository branch (`person1/core-management`) delivers the complete implementation of **Person 1 — Core Management**, owning Identity & RBAC, Customer Accounts, Product & Variant Catalogue, Subscription Plans with Price Versioning, Quotations Pipeline, Subscription Lifecycle State Machine, and the Customer Self-Service Portal.

---

## Architecture & Team Setup

| Team Role | Domain Ownership | Status |
|---|---|---|
| **Person 1 (This Branch)** | Identity/RBAC, Customer Master, Catalogue, Plans, Quotations, Subscriptions Engine, Customer Portal | **Complete & Verified** |
| **Person 2** | Tax, Discounts, Billing, Invoices, Payments | Connected via `/api/v1/internal/subscriptions/due` |
| **Person 3** | Finance Analytics, Visualizations, Revenue Guardian | Connected via `subscription_events` audit table |

---

## Key Features Implemented

### 1. Identity, Auth & Real Email OTP
- **Argon2 Password Hashing & Strict Complexity**: Enforces >8 chars (min 9), uppercase, lowercase, numeric, and special character.
- **Genuine Email OTP Verification**: 2-step customer registration with cryptographically secure 6-digit OTPs dispatched via real SMTP delivery. No universal or hardcoded bypasses.
- **SHA-256 Hashed OTP Storage**: Zero plaintext OTPs in database or memory.
- **Security Guardrails**: 10-minute expiry, max 5 attempts limit, 60-second resend cooldown, anti-enumeration generic responses.
- **Password Recovery**: Real email OTP password reset with authorization reset tokens.

### 2. Strict Role-Based Dashboards & Workspaces
- **Admin Workspace (`admin@example.com`)**:
  - Live system KPIs from `/api/v1/admin/stats` (Total Customers, Staff, Products, Plans, Quotes, Subscriptions breakdown).
  - Full Customer CRUD, Staff Provisioning, Catalogue & Plans configuration, Quotations, Subscriptions.
- **Staff Workspace (`staff@example.com`)**:
  - Operational workspace for customer quoting and subscription lifecycle management.
  - Strictly blocked from Staff Provisioning and administrative telemetry (403 Forbidden).
- **Customer Self-Service Portal (`customer@example.com`)**:
  - Profile management, view owned subscriptions, lifecycle self-service (Pause, Resume, Renew, Early Close gated by plan flags), and billing invoice integration.

### 3. Catalogue & Pricing Engine
- **Decimal Precision**: All pricing and monetary math uses `Decimal` / `Numeric(14,2)` to prevent floating-point rounding errors.
- **Dynamic Variant Pricing**: `effective_unit_price = sales_price + variant_adjustment >= 0`.
- **Immutable Plan Versions**: Price tiers are versioned (`plan_versions`); updating plan pricing creates a new immutable version without mutating existing subscriptions.

### 4. Quotations & Subscriptions State Machine
- **Quotation Line Snapshots**: Captures exact unit price, discount, and variant configuration at quote time.
- **Idempotent Confirmation**: Quotation confirmation creates a unique subscription (`subscriptions.quotation_id` unique constraint).
- **Lifecycle Transitions**: `DRAFT` → `QUOTATION` → `CONFIRMED` → `ACTIVE` ↔ `PAUSED` → `CLOSED`.
- **Plan Policy Gating**: Pause permitted only if `allow_pause = True`; early close permitted only if `allow_early_close = True`.
- **Audit Event Trail**: Every state change recorded in `subscription_events` with actor ID, status diff, and UTC timestamp.

### 5. Person 2 Inter-Service Billing Contract
- **Endpoint**: `GET /api/v1/internal/subscriptions/due?as_of=YYYY-MM-DD`
- **Security**: Guarded by `X-Internal-Service-Key`.
- **Month-End Date Clamping**: Deterministically handles irregular month lengths (Jan 31 → Feb 28/29 → Mar 31).

---

## Quick Start Guide

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Email Service Configuration

Copy `.env.example` to `backend/.env` and configure your SMTP credentials:

```bash
cp .env.example backend/.env
```

Edit `backend/.env`:
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True
SMTP_USE_SSL=False
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=SubscriptIQ
```
*(Refer to `docs/email-setup-guide.md` for detailed provider instructions.)*

### 3. Seed Demo Data

```bash
python scripts/seed_demo.py
```

Pre-seeded accounts:
- **Admin**: `admin@example.com` / `Admin@Secure123!`
- **Staff**: `staff@example.com` / `Staff@Secure123!`
- **Customer**: `acme@example.com` / `Customer@Secure123!`

### 4. Start Backend Server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` in your browser.

---

## Running Automated Tests

```bash
# Run backend test suite (16 unit and integration tests)
python -m pytest backend/tests -v
```

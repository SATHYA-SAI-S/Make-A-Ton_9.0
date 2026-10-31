# SubscriptIQ Inter-Module API Contracts (Person 1 -> Person 2 & Person 3)

This document specifies the frozen data contracts, date semantics, and API signatures provided by **Person 1 (Core Management)** for **Person 2 (Billing Engine & Invoicing)** and **Person 3 (Finance & Revenue Guardian)**.

---

## 1. Due Subscriptions Contract (For Person 2 Billing Engine)

### 1.1 HTTP Endpoint

- **Method:** `GET`
- **Path:** `/api/v1/internal/subscriptions/due`
- **Authentication:** Header `X-Internal-Service-Key: <INTERNAL_SERVICE_KEY>` (from environment)
- **Query Parameters:**
  - `as_of` (date, required): Target billing evaluation date (format: `YYYY-MM-DD`).
  - `cursor` (string, optional): Pagination token.
  - `limit` (integer, optional, default: 50, max: 500).

#### Example Request
```http
GET /api/v1/internal/subscriptions/due?as_of=2026-10-31 HTTP/1.1
Host: localhost:8000
X-Internal-Service-Key: subscriptiq-internal-dev-key-2026
```

#### Example Response (200 OK)
```json
{
  "items": [
    {
      "subscription_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "customer_id": "8bb1b874-9dfc-4cb3-a60d-7db0a020be84",
      "plan_id": "2bc84a89-9dbb-4df2-8cb3-1fa0b030be99",
      "plan_version_id": "4ef94b12-1fcc-4ec2-9bb3-5ab0c040cd11",
      "billing_frequency": "monthly",
      "next_billing_at": "2026-10-31",
      "currency": "INR",
      "lines": [
        {
          "product_id": "7fa85f64-5717-4562-b3fc-2c963f66afa7",
          "variant_id": "9ca85f64-5717-4562-b3fc-2c963f66afa8",
          "description": "Cloud ERP Suite - Odoo Pro Edition",
          "quantity": 5,
          "unit_price": "2560.00",
          "line_total": "12800.00"
        }
      ]
    }
  ],
  "as_of": "2026-10-31",
  "total_due": 1,
  "next_cursor": null
}
```

### 1.2 Direct Python Domain Function (Recommended for in-process Celery Workers)
```python
from app.subscriptions.service import get_due_subscriptions, advance_next_billing

# Inside billing worker task:
due_batch = get_due_subscriptions(db, as_of=today, limit=100)

for item in due_batch.items:
    # 1. Person 2 creates invoice and consumes discount
    # ...
    # 2. Advance billing schedule idempotently:
    advance_next_billing(
        db=db,
        subscription_id=item.subscription_id,
        period_start=period_start,
        period_end=period_end
    )
```

---

## 2. Date Semantics & Month-End Clamping Rules

1. **Storage:** All database timestamps (`created_at`, `updated_at`, `subscription_events.created_at`) are stored in **UTC**.
2. **Billing Decision:** Evaluated using customer / business timezone (default: `Asia/Kolkata`).
3. **Anchor Day Preservation & Month-End Clamping:**
   - When a subscription is activated on the 31st of January:
     - `billing_anchor_day = 31`
     - Billing cycle 1: `2026-01-31`
     - Billing cycle 2 (February): Clamped to `2026-02-28` (or `2026-02-29` on leap years).
     - Billing cycle 3 (March): Returns to anchor day `2026-03-31`.
     - Billing cycle 4 (April): Clamped to `2026-04-30`.
4. **Exclusions from Billing:**
   - Subscriptions in `paused`, `closed`, `draft`, or `confirmed` states are **never returned** by the due list.
   - Only subscriptions in `active` status with `next_billing_at <= as_of` are returned.

---

## 3. Subscription Lifecycle State Machine

```
      +---------+
      |  DRAFT  |
      +----+----+
           |
           v
    +--------------+
    |  QUOTATION   | ---- (Expired / Cancelled)
    +------+-------+
           |
           v (Quotation Confirm)
    +--------------+
    |  CONFIRMED   |
    +------+-------+
           |
           v (Staff Activate)
    +--------------+ <================+
    |    ACTIVE    |                  | (Resume)
    +---+------+---+                  |
        |      |                      |
(Pause) |      +------> +--------+ ---+
        |               | PAUSED |
        v               +--------+
    +--------+
    | CLOSED | (Auto-close after end date / early close)
    +--------+
```

Every state change writes an immutable audit record to `subscription_events`:
- `subscription_id`: UUID
- `actor_id`: UUID (or NULL for automated system worker jobs)
- `from_state`: string
- `to_state`: string
- `reason`: string
- `created_at`: UTC timestamp

---

## 4. Plan Price Versioning (For Person 3 Finance & MRR Analytics)

- When an admin adjusts a plan's price, existing subscriptions **do not** silently change their price.
- A new immutable row is added to `plan_versions`:
  - `id`: UUID
  - `plan_id`: UUID
  - `version_no`: integer (`1, 2, 3...`)
  - `price`: NUMERIC(14,2)
  - `effective_from`: UTC timestamp
- Quotations and Subscriptions record both `plan_id` and the specific `plan_version_id` locked in at commercial agreement time.

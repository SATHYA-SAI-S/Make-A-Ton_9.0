# Person 2: Billing & Invoicing Engine REST API Reference

SubscriptIQ Billing Engine exposes modular REST endpoints rooted at `/api/v1`. All monetary values are strictly formatted as banker-safe Decimal strings (e.g. `"1250.00"`).

---

## 1. Taxes & Company Billing Profile (`/api/v1/taxes`)

### `GET /api/v1/taxes/rules`
Lists all configured GST/tax rules.
- **Response**: `200 OK`
  ```json
  [
    {
      "id": "uuid",
      "name": "GST 18%",
      "rate": "18.00",
      "type": "GST",
      "effective_from": "2026-10-01",
      "effective_to": null,
      "active": true
    }
  ]
  ```

### `POST /api/v1/taxes/rules`
Creates a new tax rule.
- **Request Body**:
  ```json
  {
    "name": "Standard GST 18%",
    "rate": "18.00",
    "type": "GST",
    "effective_from": "2026-10-01"
  }
  ```
- **Response**: `201 Created`

### `GET /api/v1/taxes/settings`
Returns seller company details for place-of-supply origin logic.
- **Response**: `200 OK`
  ```json
  {
    "id": "default",
    "company_name": "Brightloop Software",
    "company_state_code": "KA",
    "company_gstin": "29AABCU9603R1Z7",
    "default_currency": "INR",
    "invoice_prefix": "INV",
    "invoice_sequence": 1
  }
  ```

### `POST /api/v1/taxes/preview`
Pure preview calculation of taxes without persisting records. Evaluates intra-state split (CGST+SGST) vs inter-state (IGST).

---

## 2. Discounts (`/api/v1/discounts`)

### `GET /api/v1/discounts`
Lists promotional and coupon rules.

### `POST /api/v1/discounts`
Creates a coupon/discount rule.
- **Request Body**:
  ```json
  {
    "code": "FESTIVE20",
    "name": "Festive Discount",
    "discount_type": "PERCENTAGE",
    "value": "20.00",
    "scope": "SUBSCRIPTION",
    "max_discount_amount": "500.00",
    "max_uses": 100,
    "valid_from": "2026-10-01"
  }
  ```

### `GET /api/v1/discounts/performance`
Analytics endpoint showing times redeemed, unique customers, and total monetary savings provided.

---

## 3. Billing Engine (`/api/v1/billing`)

### `POST /api/v1/billing/run`
Triggers recurring billing execution across billable subscriptions.
- **Request Body**:
  ```json
  {
    "as_of": "2026-10-31",
    "dry_run": false
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "id": "uuid",
    "started_at": "2026-10-31T07:00:00Z",
    "status": "COMPLETED",
    "subscriptions_checked": 45,
    "invoices_created": 42,
    "failures": 0
  }
  ```

### `GET /api/v1/billing/runs`
Lists historical billing runs with pagination.

### `GET /api/v1/billing/runs/{id}`
Returns itemized execution log detailing every subscription evaluated.

---

## 4. Invoices (`/api/v1/invoices`)

### `GET /api/v1/invoices`
Lists invoices with query filters (`customer_id`, `status`, `page`, `page_size`).

### `GET /api/v1/invoices/{id}`
Returns complete invoice details including customer, seller, lines, snapshot JSON, and payment balance.

### `POST /api/v1/invoices/{id}/confirm`
Finalizes a `DRAFT` invoice into `CONFIRMED` state.

### `POST /api/v1/invoices/{id}/cancel`
Cancels an unpaid invoice. Requires cancellation `reason`.

### `GET /api/v1/invoices/{id}/pdf`
Streams dynamic PDF generated with ReportLab (`Content-Type: application/pdf`).

### `GET /api/v1/invoices/{id}/printable`
Renders standalone HTML template optimized for browser printing (`window.print()`).

---

## 5. Payments & Split Allocation (`/api/v1/payments`)

### `POST /api/v1/payments`
Captures payment with optional split allocations.
- **Request Body**:
  ```json
  {
    "customer_id": "cust-001",
    "method": "UPI",
    "amount": "1500.00",
    "reference": "UPI-REF-9988",
    "allocations": [
      { "invoice_id": "inv-001", "amount": "1000.00" },
      { "invoice_id": "inv-002", "amount": "500.00" }
    ]
  }
  ```

### `POST /api/v1/payments/{id}/allocate`
Applies unallocated advance credits from an existing payment to one or more invoices.

### `POST /api/v1/payments/{id}/refund`
Processes full or partial refund, reversing allocations in LIFO order and restoring invoice balances.

### `POST /api/v1/payments/create-order`
Generates test-mode gateway order.

### `POST /api/v1/payments/webhook`
Idempotent webhook handler with HMAC SHA-256 signature verification (`x-gateway-signature` or `x-razorpay-signature`).

---

## 6. Overdue & Reminders (`/api/v1/overdue`)

### `GET /api/v1/overdue/invoices`
Lists all overdue invoices with calculated `days_overdue` and `tier` (1, 2, or 3).

### `GET /api/v1/overdue/summary`
Returns collection recovery metrics and tier breakdown.

### `POST /api/v1/overdue/trigger-reminders`
Evaluates overdue invoices and dispatches templated notification emails without duplicates.

### `POST /api/v1/overdue/followups`
Logs manual debt collection notes, call status, and promised payment dates.

### `GET /api/v1/overdue/followups/{invoice_id}`
Returns complete follow-up audit trail for an invoice.

---

## 7. Reconciliation (`/api/v1/reconciliation`)

### `GET /api/v1/reconciliation/report`
Audits total payments, allocations, invoice balances, and flags discrepancies.
- **Response**: `200 OK`
  ```json
  {
    "is_healthy": true,
    "discrepancies_count": 0,
    "total_payments_checked": 120,
    "total_invoices_checked": 95,
    "metrics": {
      "total_payment_volume": "150000.00",
      "total_unallocated_volume": "5000.00",
      "total_invoice_balance": "15000.00",
      "total_invoice_paid": "145000.00"
    },
    "discrepancies": []
  }
  ```

### `POST /api/v1/reconciliation/allocate-unallocated`
Auto-allocates customer advance credits against oldest open invoices FIFO.

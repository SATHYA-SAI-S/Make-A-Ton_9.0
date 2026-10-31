# SubscriptIQ — Person 3 API Contracts & Schema Specifications
**Module:** Finance Intelligence, Customer Portal, Revenue Guardian & Audit  
**Base URL:** `/api/v1`  
**Standard Response Wrap:**
- Lists: `{ "items": [...], "total": 120, "page": 1, "page_size": 20 }`
- Errors: `{ "error": { "code": "RESOURCE_NOT_FOUND", "message": "Subscription not found", "details": {} } }`

---

## 1. Audit Service (`/api/v1/audit`)

### `GET /api/v1/audit/logs`
- **Roles:** `admin`, `staff` (with audit permission)
- **Query Params:** `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `start_date`, `end_date`, `page`, `page_size`
- **Response:**
```json
{
  "items": [
    {
      "id": "e674b931-10d4-42b7-a36c-947ca793a001",
      "occurred_at": "2026-10-31T10:15:30Z",
      "actor_id": "42861a45-b46f-4a34-a3f2-8419adfb1102",
      "actor_role": "admin",
      "action": "plan.price_updated",
      "entity_type": "plan",
      "entity_id": "plan_enterprise_yearly",
      "before": { "price": "120000.00" },
      "after": { "price": "144000.00" },
      "meta": { "ip": "192.168.1.10", "reason": "Annual inflation adjustment" },
      "request_id": "req-9872134"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### `GET /api/v1/audit/logs/{id}`
- **Response:** Single audit log entry with detailed before/after diff summary.

---

## 2. Customer Portal (`/api/v1/portal`)

*Protected by `require_roles("customer")`. The `customer_id` is automatically extracted from JWT claims via `CustomerPort.get_by_user`. Requesting another customer's ID returns 403 Forbidden or 404 Not Found.*

### `GET /api/v1/portal/dashboard`
- **Response:**
```json
{
  "customer": {
    "id": "cust-101",
    "name": "Acme Technologies",
    "email": "billing@acme.com"
  },
  "summary": {
    "active_subscriptions_count": 2,
    "outstanding_balance": "12500.00",
    "unpaid_invoices_count": 1,
    "next_renewal_date": "2026-11-15"
  },
  "recent_invoices": [...],
  "active_subscriptions": [...]
}
```

### `GET /api/v1/portal/subscriptions`
- **Response:** List of subscriptions for the logged-in customer.

### `GET /api/v1/portal/subscriptions/{id}`
- **Response:** Subscription details including plan terms, line items, and activity timeline.

### `GET /api/v1/portal/invoices`
- **Response:** List of invoices for the logged-in customer.

### `GET /api/v1/portal/invoices/{id}/pdf`
- **Response:** PDF binary download (`application/pdf`) with `Content-Disposition`.

### `GET /api/v1/portal/payments`
- **Response:** Payment history and allocation breakdown.

---

## 3. Customer Requests (`/api/v1/portal/requests`)

### `POST /api/v1/portal/requests`
- **Roles:** `customer`
- **Body:**
```json
{
  "subscription_id": "sub-1002",
  "type": "UPGRADE",
  "target_plan_id": "plan_pro_yearly",
  "note": "Upgrading to Pro Yearly for additional API limits."
}
```
- **Allowed Types:** `UPGRADE`, `DOWNGRADE`, `PAUSE`, `CANCEL`, `RENEWAL`

### `GET /api/v1/portal/requests`
- **Roles:** `customer` (sees own requests) or `staff`/`admin` (sees all requests, filterable by status: `PENDING`, `APPROVED`, `REJECTED`, `APPLIED`).

### `POST /api/v1/portal/requests/{id}/review`
- **Roles:** `admin`, `staff`
- **Body:**
```json
{
  "action": "APPROVE",
  "reason": "Approved customer requested annual upgrade."
}
```

---

## 4. Finance Intelligence Overview (`/api/v1/finance/overview`)

### `GET /api/v1/finance/overview`
- **Roles:** `admin`, `staff`
- **Query Params:** `start_date`, `end_date`, `plan_id`, `frequency`, `customer_id`, `status`
- **Response:**
```json
{
  "kpis": {
    "mrr": { "value": "184500.00", "previous": "162000.00", "change_pct": 13.88 },
    "arr": { "value": "2214000.00", "previous": "1944000.00", "change_pct": 13.88 },
    "active_subscriptions": { "value": 142, "previous": 128, "change_pct": 10.93 },
    "active_customers": { "value": 118, "previous": 110, "change_pct": 7.27 },
    "arpc": { "value": "1563.56", "previous": "1472.72", "change_pct": 6.16 },
    "revenue_received": { "value": "245000.00", "previous": "210000.00", "change_pct": 16.66 },
    "total_invoiced": { "value": "260000.00", "previous": "225000.00", "change_pct": 15.55 },
    "outstanding_balance": { "value": "45000.00", "previous": "52000.00", "change_pct": -13.46 },
    "overdue_amount": { "value": "18000.00", "previous": "22000.00", "change_pct": -18.18 },
    "overdue_count": { "value": 6, "previous": 8, "change_pct": -25.0 },
    "collection_rate_pct": { "value": 94.23, "previous": 91.50, "change_pct": 2.73 },
    "customer_churn_rate_pct": { "value": 2.14, "previous": 2.80, "change_pct": -0.66 }
  },
  "period": { "start": "2026-10-01", "end": "2026-10-31" }
}
```

---

## 5. Visualizations & Analytical Charts (`/api/v1/finance/charts`)

Each chart endpoint returns data formatted for visualization along with structured drill-down links.

| # | Endpoint | Description |
|---|---|---|
| 1 | `/revenue-performance` | Invoiced vs Collected revenue over time |
| 2 | `/subscription-distribution` | Distribution by billing frequency & plan tier |
| 3 | `/invoice-aging` | Unpaid balance categorized by aging buckets (Current, 1-30, 31-60, 61-90, 90+) |
| 4 | `/subscription-growth` | New, Renewed, and Closed subscriptions per month |
| 5 | `/mrr-trend` | Monthly MRR & ARR evolution with rolling average |
| 6 | `/mrr-waterfall` | Breakdown: Starting MRR + New + Expansion - Contraction - Churn = Ending MRR |
| 7 | `/cohorts` | Customer monthly cohort retention heatmap matrix |
| 8 | `/concentration` | Top 10 customer revenue & MRR Pareto distribution |
| 9 | `/collection-funnel` | Invoice conversion: Generated -> Confirmed -> Partially Paid -> Paid |
| 10 | `/forecast` | Baseline versus simulation projection curves |

---

## 6. Financial Forecasting Simulator (`/api/v1/finance/forecast`)

### `POST /api/v1/finance/forecast/simulate`
- **Body:**
```json
{
  "horizon_months": 12,
  "assumptions": {
    "new_growth_pct": 12.0,
    "churn_pct": 3.0,
    "expansion_pct": 4.0,
    "contraction_pct": 1.0,
    "collection_rate_pct": 92.0,
    "price_increase_pct": 0.0
  }
}
```
- **Response:**
```json
{
  "baseline": [...],
  "projection": [
    {
      "month": "2026-11",
      "mrr": "202950.00",
      "arr": "2435400.00",
      "projected_invoiced": "210000.00",
      "projected_collected": "193200.00",
      "projected_outstanding": "16800.00",
      "step_explanation": "Starting MRR 184500 * (1 + 0.12 - 0.03 - 0.01) + expansion 7380.00"
    }
  ],
  "summary": { "projected_annual_growth_pct": 28.4 }
}
```

---

## 7. Revenue Guardian (`/api/v1/guardian`)

### `GET /api/v1/guardian/dashboard`
- **Response:**
```json
{
  "summary": {
    "total_open_alerts": 8,
    "critical_count": 2,
    "high_count": 3,
    "medium_count": 2,
    "low_count": 1,
    "total_estimated_impact": "64800.00"
  },
  "recent_runs": [...],
  "top_alerts": [...]
}
```

### `GET /api/v1/guardian/alerts`
- **Query Params:** `status`, `severity`, `category`, `rule_key`, `page`, `page_size`

### `POST /api/v1/guardian/alerts/{id}/action`
- **Body:**
```json
{
  "action": "RESOLVE",
  "note": "Verified invoice INV-2026-0041 was re-issued and reconciled."
}
```

### `POST /api/v1/guardian/run`
- **Description:** Triggers immediate detection cycle across all 8 rules.

# SubscriptIQ — Person 3 Financial Metrics & KPI Specifications
**Author:** Person 3 (Finance Intelligence & Analytics)  
**Contract Version:** 1.0.0  
**Target:** Standardized Calculation Formulas across APIs, Visualizations & Reporting

---

## 1. MRR (Monthly Recurring Revenue) & Normalization

### Normalization Convention
SubscriptIQ supports four billing frequencies: `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY`.  
All subscription line prices are normalized into an exact monthly equivalent using standard financial conventions:

$$\text{Normalized Price} = \begin{cases} 
\text{Price} \times \frac{365}{12} & \text{if Frequency} = \text{DAILY} \\
\text{Price} \times \frac{52}{12} & \text{if Frequency} = \text{WEEKLY} \\
\text{Price} & \text{if Frequency} = \text{MONTHLY} \\
\frac{\text{Price}}{12} & \text{if Frequency} = \text{YEARLY}
\end{cases}$$

### Line Price Calculation
For any subscription $S$, line price is computed from the contract price snapshot:
$$\text{Price}(S) = \sum_{l \in \text{lines}(S)} \Big( \text{quantity}(l) \times \text{unit\_price}(l) \Big) - \text{Discount}_{\text{recurring}}(S)$$
*Note: Unit price is the agreed snapshot captured at subscription confirmation. It does NOT fluctuate if catalogue prices change. One-time setup fees and sales taxes are excluded from MRR.*

### Total MRR
$$\text{MRR} = \sum_{S \in \text{Active Subscriptions}} \text{Normalized Price}(S)$$
- **Included Statuses:** `ACTIVE`
- **Excluded Statuses:** `DRAFT`, `QUOTATION`, `CONFIRMED`, `PAUSED`, `CLOSED` (Expired, Early Closure, Cancelled)
- *Paused Subscriptions:* Do not generate revenue while paused, hence excluded from current active MRR.

### Total ARR (Annual Recurring Revenue)
$$\text{ARR} = \text{MRR} \times 12$$

---

## 2. Customer & Retention Metrics

### Active Customer Count
Number of distinct customers holding at least one subscription with status `ACTIVE`.
$$\text{Active Customers} = \left| \left\{ C \mid \exists S \in \text{Subscriptions}(C) \text{ where status}(S) = \text{ACTIVE} \right\} \right|$$

### ARPC (Average Revenue Per Customer)
$$\text{ARPC} = \frac{\text{MRR}}{\text{Active Customers}}$$
*(If Active Customers = 0, ARPC = 0.00)*

### Customer Churn Rate (Period $P$)
$$\text{Customer Churn Rate} = \frac{\text{Lost Customers in } P}{\text{Active Customers at start of } P} \times 100$$
A customer is classified as **Lost** when their last remaining `ACTIVE` subscription transitions to `CLOSED` (reasons: `EXPIRED`, `EARLY_CLOSURE`, or `CANCELLED`) during period $P$, leaving them with zero active subscriptions.

### MRR Churn Rate (Period $P$)
$$\text{MRR Churn Rate} = \frac{\text{Churned MRR in } P}{\text{Starting MRR of } P} \times 100$$

---

## 3. Cash Flow, Invoicing & Collection Metrics

### Revenue Received (Cash Inflow)
The net cash received from customers during period $P$:
$$\text{Revenue Received} = \sum_{\substack{p \in \text{Payments} \\ \text{status}(p) = \text{RECORDED} \\ \text{date}(p) \in P}} \text{amount}(p) - \sum_{\substack{r \in \text{Refunds} \\ \text{date}(r) \in P}} \text{amount}(r)$$
- **Included:** Payments with status `RECORDED` (UPI, Card, Bank Transfer, Cash).
- **Excluded:** Failed payments (`FAILED`). Partial payments count for the exact amount received.

### Total Invoiced
$$\text{Total Invoiced} = \sum_{\substack{i \in \text{Invoices} \\ \text{status}(i) \neq \text{CANCELLED} \\ \text{invoice\_date}(i) \in P}} \text{total}(i)$$

### Outstanding Balance
The sum of remaining unpaid balances across all confirmed invoices:
$$\text{Outstanding} = \sum_{\substack{i \in \text{Invoices} \\ \text{status}(i) \in \{\text{CONFIRMED}, \text{PARTIALLY\_PAID}\}}} \text{balance}(i)$$
$$\text{balance}(i) = \text{total}(i) - \text{amount\_paid}(i)$$

### Overdue Invoices
An invoice is considered **Overdue** when:
$$\text{status}(i) \in \{\text{CONFIRMED}, \text{PARTIALLY\_PAID}\} \quad \land \quad \text{balance}(i) > 0 \quad \land \quad \text{due\_date}(i) < \text{Current Date}$$
$$\text{Overdue Amount} = \sum_{i \in \text{Overdue Invoices}} \text{balance}(i)$$

### Collection Rate (%)
$$\text{Collection Rate} = \frac{\text{Collected Amount in } P \text{ towards Invoices Due in } P}{\text{Total Amount Due in } P} \times 100$$
Where "Amount Due in $P$" represents invoices whose `due_date` falls inside period $P$.

---

## 4. MRR Movement Waterfall Components

For any reporting month, changes in MRR are decomposed into four atomic movements:

1. **New MRR:** MRR from subscriptions confirmed and activated in the period for customers who had no prior subscription.
2. **Expansion MRR:** Net increase in MRR from existing customers upgrading plan tiers, increasing seat quantities, or purchasing recurring add-on lines.
3. **Contraction MRR:** Net decrease in MRR from existing customers downgrading plan tiers or decreasing seat quantities (without full cancellation).
4. **Churned MRR:** Total MRR lost from subscriptions that closed (`EXPIRED`, `EARLY_CLOSURE`, `CANCELLED`) during the period.

$$\text{Ending MRR} = \text{Starting MRR} + \text{New MRR} + \text{Expansion MRR} - \text{Contraction MRR} - \text{Churned MRR}$$

---

## 5. Aging Buckets Convention
Unpaid invoice balances are classified into standard aging intervals based on days past `due_date`:

| Bucket | Days Overdue Range | Risk Weight |
|---|---|---|
| **Current** | $\text{due\_date} \ge \text{today}$ (Not overdue) | Low |
| **1 – 30 Days** | $1 \le (\text{today} - \text{due\_date}) \le 30$ | Moderate |
| **31 – 60 Days** | $31 \le (\text{today} - \text{due\_date}) \le 60$ | High |
| **61 – 90 Days** | $61 \le (\text{today} - \text{due\_date}) \le 90$ | Severe |
| **90+ Days** | $(\text{today} - \text{due\_date}) > 90$ | Critical |

---

## 6. Precision & Rounding Standard
1. All monetary fields are computed and stored as **Python `Decimal` / SQL `Numeric(14,2)`**.
2. Floating-point numbers (`float`) are strictly disallowed for currency values.
3. Rounding uses **`ROUND_HALF_UP`** (bankers' compliant rounding to 2 decimal places).
4. In API JSON responses, all financial totals are serialized as standard decimal strings (e.g. `"14999.50"` or formatted as currency objects `{ "currency": "INR", "amount": "14999.50" }`).

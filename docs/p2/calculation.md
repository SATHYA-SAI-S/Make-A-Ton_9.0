# SubscriptIQ: Pricing Calculation Specification

## 1. Overview
The pricing calculator (`backend/app/billing/calculator.py`) is a pure functional calculation engine designed to determine invoice line subtotals, itemized discounts, applicable taxes, and the final invoice total. It strictly enforces financial invariants:
- **Zero Floating-Point Operations**: All calculations use Python's `Decimal` type.
- **Banker-Safe Rounding**: `ROUND_HALF_UP` is applied at every rounding boundary to prevent penny loss or systemic drift.

---

## 2. Order of Execution
Calculations must proceed in the following exact chronological order:

```
[ Line Unit Price Snapshot ] x [ Quantity ]
              │
              ▼
      [ Line Subtotal ]
              │
              ▼
  [ - Product-Specific Discount ]
              │
              ▼
  [ - Subscription-Wide Discount ] (pro-rated across eligible bases)
              │
              ▼
     [ Discounted Taxable Base ]
              │
              ▼
      [ + Taxes Applied ] (Place of Supply: CGST + SGST or IGST)
              │
              ▼
      [ Line Final Total ]
```

### Detailed Formulae
1. **Raw Line Subtotal**:
   $$\text{subtotal}_i = \text{quantize}(\text{unit\_price}_i \times \text{quantity}_i)$$

2. **Product Discount**:
   Applied directly to the matching line item:
   $$\text{base}_i^{(1)} = \max(0, \text{subtotal}_i - \text{product\_discount}_i)$$

3. **Subscription-Wide Discount**:
   Distributed across lines proportionally to their remaining taxable base:
   $$\text{discount}_{i}^{\text{sub}} = \text{quantize}\left(\text{sub\_discount} \times \frac{\text{base}_i^{(1)}}{\sum_j \text{base}_j^{(1)}}\right)$$
   Any remainder penny from division is assigned to the final line item to guarantee the sum of line discounts equals the total subscription discount.

4. **Tax Calculation**:
   Taxes are computed strictly on the post-discount taxable base:
   $$\text{tax}_i = \text{quantize}\left(\text{discounted\_base}_i \times \frac{\text{tax\_rate}}{100}\right)$$

5. **Final Aggregates**:
   $$\text{Total} = \sum \text{subtotal}_i - \sum \text{discount}_i + \sum \text{tax}_i$$

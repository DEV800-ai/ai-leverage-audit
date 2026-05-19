# Neighborhood Supermarket — AI Playbook v1

An independent neighborhood supermarket with 800 SKUs. The owner manages purchasing, supplier relations, and daily operations. The goal is to streamline processes and reduce manual errors.

**Primary goal:** Reduce invoice processing time to under 1 hour per week and prevent missed supplier price changes.

_✅ Accepted by the audit_

## Your weekly workflows

| Workflow | Frequency | Volume | Time |
| --- | --- | --- | --- |
| **Invoice Processing** (invoice-processing) | weekly | 1/wk × 150min | ~150min/wk |
| **Stock Replenishment** (stock-replenishment) | weekly | 1/wk × 60min | ~60min/wk |
| **Supplier Communication** (supplier-communication) | event_driven | 1/wk × 30min | ~30min/wk |
| **Cash Reconciliation** (cash-reconciliation) | daily | 7/wk × 30min | ~210min/wk |
| **Staff Training and Promotion Planning** (staff-training-and-promotion-planning) | weekly | 1/wk × 60min | ~60min/wk |

## Where AI can save you the most time

### #1 — Invoice Processing · _confidence: high_
_Significant time savings in manual invoice entry._

- Estimated time saved: **~2.5h/wk**
- Risk if AI gets it wrong: high · Setup complexity: medium · Human judgment needed: high
- Suggested mix: **40% automate** / 30% assist / **30% keep human**
- Evidence from your intake:
  - _Manual invoice entry is time-consuming_
  - _Product name mismatches cause errors_
- Assumptions (intake didn't say):
  - AI can accurately scan invoices
  - Automate: Auto-fill invoice data, Match product names
  - Assist: Highlight price changes
  - Keep human: Final approval of entries

### #2 — Stock Replenishment · _confidence: medium_
_Automating order generation saves time and reduces errors._

- Estimated time saved: **~1.0h/wk**
- Risk if AI gets it wrong: medium · Setup complexity: low · Human judgment needed: medium
- Suggested mix: **50% automate** / 30% assist / **20% keep human**
- Evidence from your intake:
  - _Invoice entry errors affect stock count_
- Assumptions (intake didn't say):
  - AI can predict stock needs accurately
  - Automate: Generate order based on sales data
  - Assist: Suggest order adjustments
  - Keep human: Approve final order

### #3 — Supplier Communication · _confidence: medium_
_AI can streamline routine supplier communications._

- Estimated time saved: **~0.5h/wk**
- Risk if AI gets it wrong: low · Setup complexity: low · Human judgment needed: medium
- Suggested mix: **30% automate** / 40% assist / **30% keep human**
- Evidence from your intake:
  - _Respond to supplier queries and delivery issues_
- Assumptions (intake didn't say):
  - AI can handle simple queries
  - Automate: Auto-respond to common queries
  - Assist: Draft responses for review
  - Keep human: Handle complex issues

## Your 30-day bet

### Automate Product Name Matching in Invoice Processing

> If we automate the product name matching in invoice processing via AI, we will see a reduction in product name mismatch errors within 30 days.

| | |
| --- | --- |
| **Target workflow** | `invoice-processing` |
| **Success metric** | Reduce product name mismatch errors by 50% from the current baseline of 1 error per 3 invoices. |
| **Failure metric** | Product name mismatch errors remain above 1 error per 3 invoices after 30 days. |
| **Time investment** | 2h/wk (within your 3h/wk budget) |
| **Setup cost** | $50 (within your $60/mo budget) |
| **Expected asset by day 30** | A semi-automated system for product name matching in invoice processing, reducing manual errors. |

#### Weekly plan

1. **Week 1** — Identify and document common product name mismatches from past invoices.
2. **Week 2** — Implement AI tool to auto-suggest product name matches during invoice entry.
3. **Week 3** — Test and refine AI suggestions with real-time invoice entries.
4. **Week 4** — Evaluate error reduction and gather feedback from the owner.

#### First 48 hours — start here

- [ ] List 5 most common product name mismatches from recent invoices.
- [ ] Schedule a 30-minute meeting with an AI tool consultant to discuss feasibility.
- [ ] Draft a simple flowchart of the current invoice entry process.

## Areas to keep human-controlled

- **Inventory updates** _(severity: high)_ — Ensure accuracy and prevent stock errors
- **Final purchase order** _(severity: high)_ — Avoid incorrect orders and financial loss
- **Pricing changes** _(severity: high)_ — Prevent unauthorized price alterations

## Owner-agency checkpoints

- **When:** Invoice data auto-fill _(per_event)_
  **Do:** Owner reviews and approves entries
- **When:** Order generation _(weekly)_
  **Do:** Owner approves final order
- **When:** Price change detection _(per_event)_
  **Do:** Owner verifies and confirms changes

## Weekly self-review questions

- Have all inventory updates been verified?
- Were all purchase orders approved before sending?
- Did any unauthorized price changes occur?
- Were all automated entries reviewed?
- Are there any supplier communication issues?

## Playbook — workflow status at day 0

| Workflow | Status | Notes |
| --- | --- | --- |
| Invoice Processing | `experimenting` | Automate invoice processing to reduce errors and save time. |
| Stock Replenishment | `not_yet_tested` | Automate stock order generation to maintain optimal inventory levels. |
| Supplier Communication | `not_yet_tested` | Streamline supplier communication to resolve issues efficiently. |
| Cash Reconciliation | `not_yet_tested` | Automate cash reconciliation to ensure accurate financial records. |
| Staff Training and Promotion Planning | `not_yet_tested` | Assist in planning staff training and promotions. |

### Open questions

- How accurate is the AI in matching product names?
- What are the potential risks of incorrect data entry?
- How will the AI handle unexpected supplier queries?

### Rules for human involvement

- Owner reviews and approves entries for invoice data auto-fill.
- Owner approves final order for order generation.
- Owner verifies and confirms changes for price change detection.

---

_The artifact meets all rubric criteria, demonstrating a well-structured and specific approach to improving the supermarket's operations._

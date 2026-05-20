# Local Dental Clinic — AI Playbook v1

A local dental clinic focused on general dentistry and patient care. Managed by a practicing dentist, the clinic aims to enhance patient communication and reduce administrative workload.

**Primary goal:** Reduce administrative workload and missed follow-ups while maintaining personalized patient communication.

_✅ Accepted by the audit_

## Your weekly workflows

| Workflow | Frequency | Volume | Time |
| --- | --- | --- | --- |
| **Patient Communication** (patient-communication) | daily | 7/wk × 60min | ~420min/wk |
| **Appointment Management** (appointment-management) | daily | 4/wk × 30min | ~120min/wk |
| **Billing and Invoicing** (billing-and-invoicing) | weekly | 1/wk × 150min | ~150min/wk |
| **Treatment Planning** (treatment-planning) | weekly | 1/wk × 120min | ~120min/wk |
| **Inventory and Staff Management** (inventory-and-staff-management) | weekly | 1/wk × 60min | ~60min/wk |
| **Social Media and Reviews** (social-media-and-reviews) | weekly | 1/wk × 75min | ~75min/wk |

## Where AI can save you the most time

### #1 — Patient Communication · _confidence: high_
_Automating responses saves significant time on repetitive queries._

- Estimated time saved: **~7.0h/wk**
- Risk if AI gets it wrong: medium · Setup complexity: medium · Human judgment needed: medium
- Suggested mix: **40% automate** / 40% assist / **20% keep human**
- Evidence from your intake:
  - _Repeated WhatsApp questions from patients_
  - _Manual appointment reminders_
  - Automate: Auto-reply to common WhatsApp questions
  - Assist: Suggest responses for complex queries
  - Keep human: Handle sensitive patient issues

### #2 — Appointment Management · _confidence: high_
_Automating scheduling reduces manual effort significantly._

- Estimated time saved: **~2.0h/wk**
- Risk if AI gets it wrong: high · Setup complexity: medium · Human judgment needed: medium
- Suggested mix: **50% automate** / 30% assist / **20% keep human**
- Evidence from your intake:
  - _Rescheduling missed or canceled appointments_
  - Automate: Auto-schedule appointments
  - Assist: Suggest rescheduling options
  - Keep human: Handle last-minute cancellations

### #3 — Billing and Invoicing · _confidence: medium_
_AI can track invoices but human oversight is crucial._

- Estimated time saved: **~2.5h/wk**
- Risk if AI gets it wrong: high · Setup complexity: high · Human judgment needed: high
- Suggested mix: **30% automate** / 40% assist / **30% keep human**
- Evidence from your intake:
  - _Following up on unpaid bills_
- Assumptions (intake didn't say):
  - Assumed AI can integrate with current Excel setup
  - Automate: Auto-generate invoices
  - Assist: Flag overdue payments
  - Keep human: Verify insurance claims

## Your 30-day bet

### Automate Initial WhatsApp Responses to Common Patient Queries

> If we automate initial WhatsApp responses to common patient queries using pre-set templates, we will see a reduction in response time and administrative workload within 30 days.

| | |
| --- | --- |
| **Target workflow** | `patient-communication` |
| **Success metric** | Reduce time spent on WhatsApp responses by 40% from your Week 1 measured average. |
| **Failure metric** | Less than 10% reduction in time spent on WhatsApp responses from your Week 1 measured average. |
| **Time investment** | 2h/wk (within your 2h/wk budget) |
| **Setup cost** | $0 (within your $150/mo budget) |
| **Expected asset by day 30** | A set of automated response templates for the top 10 common patient queries integrated into WhatsApp Business. |

#### Weekly plan

1. **Week 1** — Identify and list the top 10 most common patient queries received via WhatsApp.
2. **Week 2** — Draft and refine response templates for each of the identified common queries.
3. **Week 3** — Implement the templates into WhatsApp Business auto-reply settings and test functionality.
4. **Week 4** — Monitor response times and gather feedback from patients on the clarity and helpfulness of automated responses.

#### First 48 hours — start here

- [ ] Block 20 minutes on calendar to brainstorm common patient queries.
- [ ] List current step-by-step process for responding to WhatsApp messages.
- [ ] Open WhatsApp Business settings and explore auto-reply options.

## Areas to keep human-controlled

- **Final medical advice** _(severity: high)_ — Requires professional judgment and legal responsibility.
- **Sensitive patient complaints** _(severity: high)_ — Needs empathetic human interaction.
- **Treatment recommendations** _(severity: high)_ — Relies on dentist's expertise and patient history.
- **Pricing negotiations for major treatments** _(severity: medium)_ — Involves personalized financial discussions.

## Owner-agency checkpoints

- **When:** AI suggests treatment plan _(per_event)_
  **Do:** Dentist reviews and approves.
- **When:** AI schedules appointment _(per_event)_
  **Do:** Receptionist confirms with patient.
- **When:** AI flags unpaid invoice _(weekly)_
  **Do:** Finance team verifies and follows up.

## Weekly self-review questions

- Were any sensitive complaints handled by AI?
- Did AI suggest incorrect treatment recommendations?
- Were all major pricing negotiations human-led?
- Did AI misinterpret any patient queries?
- Were there any scheduling conflicts caused by AI?

## Playbook — workflow status at day 0

| Workflow | Status | Notes |
| --- | --- | --- |
| Patient Communication | `experimenting` | Automate initial WhatsApp responses to common patient queries. |
| Appointment Management | `not_yet_tested` | Automate scheduling and rescheduling of appointments. |
| Billing and Invoicing | `not_yet_tested` | Automate invoice generation and track unpaid bills. |
| Treatment Planning | `not_yet_tested` | Assist in drafting treatment plans and cost estimates. |
| Inventory and Staff Management | `not_yet_tested` | Automate supply orders and staff scheduling. |
| Social Media and Reviews | `not_yet_tested` | Automate social media posts and review responses. |

### Open questions

- How will patients respond to automated WhatsApp messages?
- What are the risks of misinterpretation in auto-replies?
- How can we ensure AI scheduling accuracy?

### Rules for human involvement

- Dentist reviews and approves AI-suggested treatment plans.
- Receptionist confirms with patient for AI-scheduled appointments.
- Finance team verifies AI-flagged unpaid invoices.

---

_The artifact meets all rubric criteria, demonstrating a well-structured and specific approach to automation in the dental clinic._

# Product Lifecycle: 3 Stages Only

The product must stay understandable as a three-stage loop. Do not expand the lifecycle beyond these three stages.

```
Diagnose → Test → Evolve
```

---

## Algorithmic foundation

The product is a **decision and learning layer**, not an automation builder.

Internally it is powered by:

```
Constraint-Aware Multi-Criteria Decision Analysis (MCDA)
+ Sequential Experimentation
+ Human-in-the-loop Evaluation
```

Short name: **AI Leverage Prioritization Model**

This is a business prioritization problem under constraints — not a pure AI problem. The system chooses which workflow is worth testing first based on value, risk, owner capacity, and hard refusal constraints. It does not blindly maximise automation. The correct answer for some businesses is "no AI needed" or "fix the process first."

See `docs/SCORING_MODEL.md` for the full criteria and formula.

---

## Stage 1 — Diagnose

**Run an AI Leverage Audit.**

Outputs:
- Workflow Map
- AI Leverage Score
- AI-to-Human Ratio
- Keep-Human Areas
- Top Opportunities
- One 30-Day Bet

Goal:
Identify where AI creates real business leverage and where it should not be used.

Central question:
> Where can AI create real value — and where should it not be touched?

---

## Stage 2 — Test

**Run one focused 30-day experiment.**

Outputs:
- One hypothesis
- One workflow
- Success metric
- Failure metric
- Weekly review questions
- Owner feedback
- Evidence of usefulness or failure

Goal:
Validate whether the recommendation creates real value before building tools or automation.

Central question:
> Did this actually save time / increase revenue / reduce pain — or was it a nice-to-have?

---

## Stage 3 — Evolve

**Update the Business AI Maturity Profile and Playbook.**

Outputs:
- Business AI Maturity Profile
- Recommended AI Stack
- Reusable Playbook
- What Not To Automate
- Next Best Bet
- Implementation Path

For each recommended workflow the system routes to one of:

```
manual AI assist
existing SaaS
no-code template
n8n / Make / Zapier workflow
open-source tool
partner install
custom app
do not build yet
```

Default principle: recommend the smallest implementation path that can validate value. Do not recommend custom AI tools by default.

Goal:
After 1–2 loops, the system understands the right level of AI adoption for this business:

```
No AI needed here
→ AI Assist only
→ Semi-automation with human review
→ Operational automation
```

The system must be able to say "no AI needed" or "fix the process first." Not every business needs more automation.

Central question:
> What is the right level of AI for this business right now?

---

## Human agency principle

The system does not ask "What can AI automate?"

The system asks: **"Which workflow should this business safely test first — if any?"**

AI should increase owner clarity and control, not create dependence or hidden risk. The system explicitly captures what the owner refuses to automate, what assumptions it is making, and where its confidence is low.

---

## Implementation status

| Stage | Status |
| --- | --- |
| Stage 1 — Diagnose | ✅ Implemented. `audit run` produces all Stage 1 outputs. |
| Stage 2 — Test | ✅ Partially. The 30-day bet is designed and scored. Weekly check-in and owner feedback collection are manual (template-based). |
| Stage 3 — Evolve | ✅ Implemented. `audit reflect` runs the continuation audit after a 30-day bet. Maturity profile and recommended AI stack are designed outputs, not yet produced as typed artifacts. |

---

## Related docs

- `docs/SCORING_MODEL.md` — MCDA criteria, formula, and hard constraints
- `docs/BUSINESS_MODEL.md` — customer flow, pricing tiers, package scope
- `docs/CYCLES.md` — technical design for the Evolve loop

---

## Product sentence

> We help small businesses diagnose where AI actually helps, test one low-risk workflow, and evolve toward the right level of AI adoption over time.

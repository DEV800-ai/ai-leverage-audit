# Business Model

## Customer-facing flow

The customer never sees agents, schemas, JSON, workflows, or internal runtime concepts.

Their experience is:

```
Tell us about your business
→ Get an AI Leverage Audit
→ Choose one 30-day bet
→ Track the bet
→ Build your Business AI Playbook
```

---

## Entry points and pricing

| Product | Price | Stage |
| --- | --- | --- |
| AI Leverage Audit | $20 one-time | Diagnose only |
| AI Operating Mentor | $100/month | Diagnose + Test + Evolve (ongoing) |
| AI Operating Setup Package | $500 fixed-scope | Diagnose + one full Test + Evolve cycle |

### $20 — AI Leverage Audit

A low-friction entry product. Owner fills in the intake, receives a one-time audit report:

- Workflow Map
- AI Leverage Score per workflow
- Keep-Human Areas
- Top 3 Opportunities
- One recommended 30-day bet

Useful on its own. Incomplete by itself — it leads naturally to Stage 2.

### $100/month — AI Operating Mentor

Ongoing access to the full Diagnose → Test → Evolve loop. Each month:

- One 30-day bet active
- Weekly review questions
- Outcome report at day 30
- Continuation audit for the next cycle

Continues until the owner's AI playbook is stable.

### $500 — AI Operating Setup Package

Fixed-scope engagement. Includes:

```
Diagnose              — AI Leverage Audit
One 30-day bet        — Designed, tracked, and reviewed
Outcome report        — What worked, what didn't
Business AI Maturity Profile
Business AI Playbook v1
Recommended AI Stack
Next 90-day roadmap
```

Does not include:

```
Custom tool development
Ongoing automation maintenance
Unlimited support
Direct customer-facing automation
Building n8n / Zapier workflows unless separately scoped
```

---

## What the product is not

- Not an automation builder
- Not an n8n / Make / Zapier competitor
- Not a custom app builder
- Not a marketplace

It is a **decision and learning layer**. It tells the owner what to test and whether it worked — not how to build it.

---

## When the audit recommends no bet

Sometimes the correct output is: "No AI experiment is ready for this business right now."

Reasons this can happen:

- All high-value workflows have high error risk and high human judgment dependency
- Budget or time does not support a meaningful experiment
- The workflow is not consistent enough to automate (process not mature)
- Owner technical readiness is too low for the available tools

This is an honest, valuable output — not a product failure. The owner learns what to fix before coming back.

---

## Customer flow diagram

```
Landing Page
    │
    ├─ $20 AI Leverage Audit
    ├─ $100/mo AI Operating Mentor
    └─ $500 Fixed AI Operating Setup
            │
            ▼
    Business Intake
    (Tell us about your business)
            │
            ▼
    Stage 1 — Diagnose
    Workflow Map · Leverage Scores · Top 3 · 30-Day Bet
            │
            ▼
    Audit Report delivered
            │
    Continue? ──No──► Save report, follow up later
            │
           Yes
            │
            ▼
    Stage 2 — Test
    Pick workflow · Define hypothesis · Track 30 days
            │
            ▼
    Outcome Report
            │
            ▼
    Stage 3 — Evolve
    Maturity Profile · Playbook · Recommended Stack · Next Bet
            │
            └──────────────────────────────► Stage 2 (next cycle)
```

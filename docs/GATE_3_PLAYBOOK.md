# Gate 3 Playbook — Collecting 5 Real Intakes

**Goal:** validate that the AI Leverage Audit produces useful output on real businesses, not just the synthetic-consultant fixture. Per [`PRODUCT_ROADMAP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_ROADMAP.md) §2.3 + §3.

**You already have 1 (the synthetic consultant). You need 4 more.**

## Audience to target

Aim for spread across these shapes — one each is ideal:

| # | Shape | Examples |
| --- | --- | --- |
| 1 | Solo consultant / freelancer | branding, dev, marketing, ops |
| 2 | Small services business (1–10 ppl) | dental, accounting, marketing agency |
| 3 | E-commerce owner | Shopify shop, Etsy seller, small DTC |
| 4 | SaaS founder, pre-product-market-fit | indie hacker, two-person founding team |

You can swap one for a fifth shape if you have a better-fit contact.

## Reach-out script (DM or email)

> Hi — I'm building a small AI mentor product for solo / small-business owners. Trying to see whether it gives useful advice on real situations, not just made-up ones. Would you be willing to fill a 5–10 minute questionnaire? In return I'll send you a short report on where AI could realistically save you time and one experiment to try. No follow-up unless you want it.

Attach: [`fixtures/intakes/INTAKE_TEMPLATE.md`](../fixtures/intakes/INTAKE_TEMPLATE.md) (or paste it inline).

## Per-intake workflow

1. **Receive the response** as plain text (or markdown).
2. **Convert to AuditIntake JSON.** Save as `fixtures/intakes/real_<name>.json`. (I'll do this for you if you paste the text — it's mechanical.)
3. **Run the audit:**
   ```bash
   LLM_PROVIDER=openai LLM_MODEL=gpt-4o-mini \
   uv run audit run --intake fixtures/intakes/real_<name>.json --output reports/<name>.json
   ```
4. **Inspect the output.** If `accepted=false`, look at which rules failed (the parser/diagnoser/leverage agents are the usual culprits) and decide if it's a prompt issue or a real-data quirk worth iterating on.
5. **Share the bet with the owner.** Either send the raw JSON (technical owners) or a written summary (everyone else). What matters: the **30-day bet** — its hypothesis, success metric, failure metric, weekly plan.
6. **Schedule the 15-min conversation** to ask: *"is this bet specific to you?"* and *"would you actually try it?"*

## What to record per intake (use a spreadsheet)

For each real intake — record these in a Google Sheet or text file as you go:

| Column | Source |
| --- | --- |
| Owner name / handle | from you |
| Business shape | manual tag (solo / services / e-com / SaaS / other) |
| Intake completion time (minutes) | ask them at the end |
| Audit walltime (seconds) | from the JSON output or `time` |
| Audit cost (USD) | query `cost_usd` from `audit.db` agent_run rows |
| `EvalReport.accepted` | from `eval_report` in the JSON |
| Rules failed (if any) | from `eval_report.criteria` |
| Bet target workflow | `thirty_day_bet.target_workflow_id` |
| Bet feels specific? (1–5) | from the 15-min conversation |
| Owner attempted bet in week 1? | follow-up at day 7 |
| Re-ran within 30 days? | check for second `WorkflowRun` row |
| Self-reported usefulness (1–5) | follow-up at day 30 |

Don't add analytics; a spreadsheet is enough for 5 intakes.

## Acceptance bars (`PRODUCT_MVP.md` §7)

V1 ships when, across the 5 real intakes:

| Bar | Threshold |
| --- | --- |
| Intake completion time | <10 minutes for ≥ 4 of 5 |
| Audit footprint | 1 WorkflowRun + 7–8 AgentRuns + 7 Artifacts, all 5 runs |
| `EvalReport.accepted=true` first run | ≥ 3 of 5 |
| Owner says bet is "specific and doable" | ≥ 4 of 5 (qualitative) |
| Platform audit gaps (missing prompt_version, double-invoke errors, missing tenant) | 0 |

## When to come back to me

- **You have a response** → paste it into our chat; I'll convert to JSON, run the audit, and report.
- **A rule fails on a real intake** → tell me which rule and which intake; I'll diagnose (prompt issue vs real-data quirk).
- **An owner says the bet feels generic or wrong** → bring me the bet text + the owner's reaction; that's iteration signal.
- **You finish the 5-intake batch** → we sit down with the tracker, count against the acceptance bars, and decide Gate 3 result (ship / iterate / pivot).

## Pricing reality check

At gpt-4o-mini, ~$0.005/audit. Five real intakes + a few re-runs is ~$0.05–$0.10 total. Trivial.

For comparison, gpt-4o would be ~$0.05/audit (10x), Claude Sonnet ~$0.04/audit. Gate 3 doesn't require a more expensive model unless something noticeably breaks on mini.

# Live Owner Reaction Playbook

**Goal:** Collect real owner reactions to the audit output. This is the only remaining Gate 3 evidence gap — structural tests are done.

**Current state:** Audit pipeline structurally accepted (8/8 profiles, gpt-4o). First real owner has not yet received their audit.

---

## Reach-out script (DM or email)

> Hi — I'm building a small AI advisor for solo / small-business owners. Trying to see whether it gives useful, specific advice on real situations. Would you be willing to fill a 5–10 minute questionnaire? In return I'll send you a short report on where AI could realistically save you time, and one concrete 30-day experiment to try. No follow-up unless you want it.

Attach or paste [`fixtures/intakes/INTAKE_TEMPLATE.md`](../fixtures/intakes/INTAKE_TEMPLATE.md).

The measurement baseline section (section 4) is optional but valuable — encourage owners to fill it for the workflows that cost them the most time. It anchors the bet metrics to their own numbers.

---

## Per-owner workflow

**Step 1 — Receive intake**
Owner replies in free text (DM, email, doc). Any format is fine.

**Step 2 — Convert to JSON**
Manually convert their response to `AuditIntake` JSON. Save as `fixtures/intakes/real_<name>.json` — the `real_*.json` pattern is gitignored so live friend data never lands in git.

If the owner filled the measurement section, include their text verbatim in `measurement_context_text`. The parser agent will extract it.

**Step 3 — Run the audit**
```bash
LLM_PROVIDER=openai \
uv run audit run \
  --intake fixtures/intakes/real_<name>.json \
  --output reports/<name>.json \
  --markdown reports/<name>.md
```

Default model: gpt-4o. Do not use gpt-4o-mini for owner-facing runs — it drops required fields and misses consistency rules roughly 1 in 3 runs.

**Step 4 — Inspect before sending**
Read the generated `reports/<name>.md` yourself first. Check:
- Does the bet target one narrow sub-activity (not the whole workflow)?
- Do the success/failure metrics reference the owner's own numbers if they gave measurements?
- Does the keep-human list reflect what they said they'd refuse to automate?

If `EvalReport.accepted=false`, check which rules failed before sending anything.

**Step 5 — Send the markdown**
Send `reports/<name>.md` to the owner. It's friend-shareable — workflow map, leverage scoring, 30-day bet, keep-human areas, playbook.

**Step 6 — Send the feedback questionnaire**
Send [`AUDIT_FEEDBACK_TEMPLATE.md`](AUDIT_FEEDBACK_TEMPLATE.md) immediately after, or within 24h. Three minutes to fill. Even Part 1 alone (bet specificity + would-try) is useful.

---

## What to record per owner (spreadsheet or text file)

| Column | Source |
| --- | --- |
| Owner / handle | you |
| Business shape | tag: solo / services / retail / e-com / creator / other |
| Intake completion time (min) | ask them |
| Audit walltime (sec) | from JSON or `time` |
| Audit cost (USD) | `cost_usd` from `audit.db` agent_run rows |
| `EvalReport.accepted` | from JSON `eval_report` |
| Rules failed | from `eval_report.criteria` |
| Bet target workflow | `thirty_day_bet.target_workflow_id` |
| Bet feels specific? | from feedback Part 1 |
| Would they try it? | from feedback Part 1 |
| Usefulness score (1–5) | from feedback Part 3 |
| Day-30 check-in requested? | from feedback Part 4 |

---

## How to read feedback

When feedback comes back, focus on:

1. **Did the bet feel specific to them, or could it have been written for anyone in their field?**
   The bet is working if owners say "specific." Generic means the workflow map or leverage ranking missed something.

2. **Would they actually try it as written?**
   "Yes, with one change" is the best signal — they're engaged and already thinking about implementation. "No" means the bet is wrong or too big.

3. **What would they change?**
   Usually: make it smaller, start with fewer suppliers / clients / products. That's the MINIMALITY RULE validating in the field.

4. **What did the audit miss?**
   Tools, constraints, staff trust issues, seasonal patterns. These become improvements to the intake template or workflow diagnoser prompt.

5. **Did the keep-human list match what they'd actually refuse?**
   Mismatches here are the most important signal — they show where the risk mapper is over- or under-cautious.

See `fixtures/feedback/samples/` for 8 synthetic example responses. Patterns that repeat across them (make bet smaller, say what you're assuming, the questions you skipped) should not be tuned away by one outlier.

---

## Acceptance bars (PRODUCT_MVP.md §7)

Live owner testing is done when, across the first real owners:

| Bar | Threshold |
| --- | --- |
| Intake completion time | < 10 min for most owners |
| `EvalReport.accepted` first run | ≥ 3 of first 5 |
| Owner says bet is "specific and doable" | ≥ 4 of first 5 |
| No platform gaps (missing prompt_version, double-invoke, missing tenant) | 0 |

---

## What not to build yet

- `audit reflect` / Cycle 2 continuation — needs a real day-30 report first
- `audit convert-intake` — needs stable intake format confirmed by real owners
- Any feedback parser or dashboard — a spreadsheet is enough for 5 owners
- V2 features of any kind

Come back to `CYCLES.md` when the first owner hits day 30.

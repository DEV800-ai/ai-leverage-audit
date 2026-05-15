# Cycle 2+ — Continuation Audits

**Status:** Design sketch, 2026-05-15. Not implemented. Re-read before building once at least one friend reaches day 30.
**Companion:** `PRODUCT_VISION.md` §4 (the loop), `PRODUCT_ROADMAP.md` §4.3 (the V2 "continuous tracking" bet), `DESIGN.md` Tier 2 (`ReflectionEvent` — deferred).

## What this doc is for

V1's Audit is one-shot — intake in, bet out, done. The product vision is a recurring 30-day cycle: bet runs → owner reports outcome → next audit picks a new bet informed by what worked and what didn't.

The platform layer is already ready for cycles (multiple `WorkflowRun` rows per tenant, immutable `Artifact` history). What's missing is the product layer that makes the next audit *use* the prior cycle's outcome. This doc sketches that layer **without committing to specifics that should be set by real cycle-1 owners**.

## What's already in place (no code change needed)

| Capability | Where |
| --- | --- |
| Append-only `WorkflowRun` rows per tenant | platform `storage/sqlite.py` |
| Immutable per-cycle `Artifact` rows (each cycle's intake, bet, playbook preserved) | platform ADR-004 |
| Re-run semantics: re-running produces a new `WorkflowRun`, keeps old ones | `PRODUCT_MVP.md` §10 |
| Per-tenant cost ledger across all cycles | `leverage-platform cost --tenant X --since 90d` |
| Re-render any historical cycle | `audit render --workflow-run-id <uuid>` |

A friend running cycles 1, 2, 3, 4 produces four `WorkflowRun` rows in the same `audit.db` today. Nothing breaks. The only thing missing is intelligence: cycle 2 doesn't *know* cycle 1 happened.

## What changes for cycle ≥ 2 (product-side only)

### 1. New schema — `OutcomeReport`

```python
class OutcomeReport(BaseModel):
    prior_workflow_run_id: UUID
    prior_bet_title: str                    # for trace, not for logic

    outcome: Literal["succeeded", "failed", "mixed", "abandoned"]
    success_metric_triggered: bool
    failure_metric_triggered: bool

    actual_weekly_hours_invested: float
    actual_setup_cost_usd: int

    what_worked_text: str                   # free text, ≥30 chars
    what_surprised_text: str                # free text, ≥30 chars
    what_owner_would_change_text: str       # free text, ≥30 chars

    intent: Literal["continue", "pivot", "stop"]
```

Filled by the owner, either:
- Free-text response to a `OUTCOME_TEMPLATE.md` questionnaire that operator converts to JSON (same flow as `INTAKE_TEMPLATE.md`), OR
- An `outcome_parser_agent` that takes the prior `ThirtyDayBet` + free text → `OutcomeReport` (~$0.005). Pick this when an owner reports loosely.

### 2. Evolved schema — `Playbook` (replaces single-cycle `FirstPlaybook`)

```python
class PlaybookEntry(BaseModel):
    workflow_id: str
    current_status: Literal["not_yet_tested", "experimenting", "validated", "rejected"]
    summary: str
    cycle_introduced: int                   # when this workflow first appeared
    last_outcome_summary: str | None        # filled when a bet targeted it

class Playbook(BaseModel):
    title: str
    business_summary: str
    cycle_number: int                       # 1 for V1, 2+ for continuations
    workflow_entries: list[PlaybookEntry]
    rules_for_human_involvement: list[str]
    open_questions: list[str]
    next_review_offset_days: int = 30
```

Status transitions across cycles:
- cycle N target → status = "experimenting" during cycle N
- After cycle N reflection: target → "validated" (outcome=succeeded), "rejected" (outcome=failed), or "experimenting" again (outcome=mixed + intent=continue)
- Workflows untouched by any cycle → "not_yet_tested"
- `rejected` workflows are NOT picked as future bet targets.

### 3. Agents that change for continuation audits

| Agent | What changes |
| --- | --- |
| `intake_parser_agent` | Unchanged — but called only when owner provides a fresh intake. In cycle-2 default flow, the prior cycle's `ParsedIntake` is reused. |
| `workflow_diagnoser_agent` | Unchanged — reused from prior cycle unless owner explicitly says workflows changed. |
| `leverage_analyst_agent` | New input: `playbook` (with cycle history). Must respect `rejected` workflows (don't put them in top-3). May down-rank `validated` workflows (already won, deepen later). |
| `bet_designer_agent` | New constraint: `target_workflow_id` cannot be a `rejected` entry. Hypothesis must explicitly acknowledge the prior cycle's outcome ("Last cycle we found X; this cycle we test Y"). |
| `risk_mapper_agent` | Largely unchanged. May add risks the owner *discovered* in the prior cycle. |
| `playbook_builder_agent` | Now takes the prior `Playbook` and updates it — does NOT start from `not_yet_tested` for every entry. |
| `critic_eval_agent` | Unchanged; eval still runs after the workflow. |
| **NEW: `outcome_parser_agent`** | Optional. Parses free-text owner reflection into a structured `OutcomeReport`. Only invoked when the operator passes raw text instead of structured JSON. |

### 4. CLI sketch

```bash
# List cycles for a tenant — useful immediately, no new schemas needed.
audit history --db audit.db --tenant default

# Continuation audit, structured outcome input:
audit reflect \
  --db audit.db \
  --outcome reports/alice_cycle1_outcome.json \
  --output reports/alice_cycle2.json \
  --markdown reports/alice_cycle2.md

# Continuation audit, free-text outcome (uses outcome_parser_agent):
audit reflect \
  --db audit.db \
  --outcome-text "I shipped the FAQ bot but only 2 clients used it. Saved maybe 1h/wk not 3. Failure metric didn't trigger but neither did success." \
  --output reports/alice_cycle2.json \
  --markdown reports/alice_cycle2.md
```

`audit reflect` defaults to reusing the **most recent** cycle's parsed intake + workflow map. Pass `--new-intake <path>` only when the owner reports their business has actually changed.

### 5. Workflow orchestration (continuation)

```
OutcomeReport (parsed or LLM-extracted)
  + prior Playbook
  + prior ParsedIntake (reused)
  + prior WorkflowMap (reused)
  + (optional) updated ParsedIntake / WorkflowMap
    → leverage_analyst_agent     → LeverageAnalysis (cycle-aware)
    → bet_designer_agent         → ThirtyDayBet (cycle-aware)
    → risk_mapper_agent          → RiskAndAgencyMap (deltas)
    → playbook_builder_agent     → Playbook (updated)
    → critic_eval_agent          → EvalReport
```

Per cycle-2 run footprint: 1 new `WorkflowRun` + 5–6 new `AgentRun` rows + 5–6 new `Artifact` rows. Smaller than cycle 1 because intake_parser + workflow_diagnoser can be skipped.

## Open questions — resolve with cycle-1 owner reports, not by guessing

1. **How does an owner actually describe an outcome?** Likely messy ("kinda worked", "wasn't sure"). Determines whether `outcome_parser_agent` is necessary or if a structured form suffices.
2. **Do owners report at exactly day 30, or drift to day 20–45?** If drift is wide, the cadence framing changes.
3. **How many cycles before the playbook stabilises and bets get harder to find?** If after 3 cycles a small-business owner runs out of obvious workflows, the product loop needs a different next-step prompt ("deepen vs widen").
4. **Should `validated` workflows ever re-enter as bet targets?** A workflow that worked once might still benefit from a second iteration. Probably yes, with a higher bar.
5. **How does Hebrew/Russian/etc. localisation interact with carry-forward state?** Cycle 1 in Hebrew, cycle 2 in English on the same playbook — what's the schema language?

## Explicitly out of scope for cycle V1

- **Mid-cycle `ReflectionEvent`** (DESIGN.md Tier 2) — only end-of-cycle for V1.
- **Continuous tracking / weekly check-ins** — V2.3 in `PRODUCT_ROADMAP.md`, gated on real evidence.
- **Multi-business support** (one owner running cycles for several clients) — different tenant_id per business already covers this in the data model; the CLI doesn't need to know.
- **Web UI for owners to fill OutcomeReport** — still CLI-based for V1 distribution.

## When to come back to this doc

When the first friend hits day 30 of their bet. At that point:
1. Read this doc.
2. Ask the friend exactly what they want to report. Compare to the draft `OutcomeReport` here — adjust the schema based on what they actually say.
3. Build `audit reflect` (~2–3 hours of focused work).
4. Run cycle 2 on that friend.
5. Iterate on the agents based on whether the cycle-2 bet feels informed by cycle 1.

Do NOT build any of this speculatively. The schemas in this doc are wrong until validated against one real cycle-1 reflection.

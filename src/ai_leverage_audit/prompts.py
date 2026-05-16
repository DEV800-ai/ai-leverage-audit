"""Prompt templates for the AI Leverage Audit agents.

Each template uses `str.format(**variables)` substitution. Variables are
documented per-template. The platform forces the LLM to return JSON
matching the agent's schema, so prompts shape content, not output form.
"""

INTAKE_PARSER_PROMPT = """\
You are converting a small business owner's free-text intake into structured fields.

Raw intake (JSON):
{intake_json}

Produce a `ParsedIntake`:
- business_summary: 1-2 sentences synthesising the business.
- weekly_tasks: extract 3-15 recurring tasks. For each: title,
  estimated_time_minutes_per_week, is_customer_facing,
  is_error_sensitive, current_tool (or null).
- tools_in_use: tools mentioned in current_tools_text.
- top_pain_points: at most 5, distilled from time_sinks and
  error-sensitive areas.
- primary_goal: rewrite primary_goal_text as one sentence.
- weekly_time_budget_hours, monthly_budget_usd: copy from intake.
- refused_automation_areas: extract 1-5 ATOMIC items (one concept
  per item, ≤ 8 words each). Break compound or multi-sentence text
  into separate items. May be empty list.

Be specific to the actual business described. Do not generalise.
"""


WORKFLOW_DIAGNOSER_PROMPT = """\
You are mapping the recurring workflows of a small business.

Parsed intake (JSON):
{parsed_intake_json}

Produce a `WorkflowMap` with 3-8 `Workflow` entries. A workflow is a
CLUSTER of related recurring tasks, not a single task.

HARD COVERAGE REQUIREMENTS:
1. Every weekly_task with estimated_time_minutes_per_week >= 60 MUST
   be represented in some workflow. Do not drop large time sinks.
2. Every entry in parsed_intake.top_pain_points MUST map onto at
   least one workflow (named or described).
3. The owner's primary_goal is to reclaim hours; the map must
   surface the workflows where those hours actually live.

For each workflow:
- id: lowercase slug, alphanumeric with hyphens, unique within this
  Audit (e.g. "lead-followup", "client-invoicing").
- title: short human-readable label.
- description: 1-2 sentences.
- frequency: one of "daily" / "weekly" / "monthly" / "event_driven".
- minutes_per_occurrence and occurrences_per_week: numbers
  (fractional ok — a monthly invoice run is ~0.25 occurrences/week).
- inputs: what triggers the workflow.
- outputs: what it produces.
- pain_points: list of strings tied to this workflow specifically;
  draw from parsed_intake.top_pain_points where applicable.
- tools_used: tools currently used; subset of
  parsed_intake.tools_in_use.

Aim for 3-6 workflows for a typical solo or small-team owner.
"""


LEVERAGE_ANALYST_PROMPT = """\
You are scoring AI leverage for each workflow in a small business. Be
terse. Every field below has a length cap; respect it.

Parsed intake (JSON):
{parsed_intake_json}

Workflow map (JSON):
{workflow_map_json}

For EACH workflow in the map, produce one `WorkflowLeverage` entry in
per_workflow:

Scoring fields:
- time_saved_hours_per_week_estimate (float): plausible hours/week saved.
- risk_if_ai_gets_it_wrong: low / medium / high.
- setup_complexity: low / medium / high.
- human_judgment_needed: low / medium / high.
- rank: 1 = highest leverage. UNIQUE ranks 1..N across all workflows.
- rationale: ONE short sentence specific to this business (≤ 25 words).

Honesty fields — every entry MUST include these, and they MUST be honest:
- confidence: low / medium / high. Use "low" when the intake didn't
  give specifics about volume, duration, or current tooling. Use "high"
  ONLY when the intake gave concrete numbers and the workflow shape is
  unambiguous.
- evidence_from_intake: 1-3 short quotes or paraphrases from the
  parsed_intake that justify this entry's scores. If you can't cite
  anything specific, your confidence should be "low".
- assumptions: 0-3 short statements of what you had to assume because
  the intake didn't say. Empty list is fine ONLY if everything came
  directly from the intake.

The owner reads these. False precision is worse than honest uncertainty —
the audit's credibility depends on confidence being calibrated.

RANKING RULE (apply in order):
  1. Primary: rank by time_saved_hours_per_week_estimate, DESCENDING.
     The owner's primary_goal is to reclaim hours — a workflow that
     saves 1.5h/wk outranks one that saves 0.5h/wk even if the
     0.5h/wk option is easier to ship.
  2. Tiebreaker: prefer lower setup_complexity.
  3. Tiebreaker: prefer lower risk_if_ai_gets_it_wrong.
Do NOT rank by ease-of-experiment alone. The bet designer downstream
will weigh setup cost against the owner's budget; the ranking should
reflect WHERE THE HOURS LIVE, not where the experiment is easiest.

Mix fields — apply these hard constraints in order:
1. automate_pct + assist_pct + keep_human_pct must sum to EXACTLY 100.
2. CONSISTENCY RULE (mandatory): if human_judgment_needed = "high",
   then keep_human_pct MUST be >= 30. Set keep_human BEFORE filling
   the other two. Do not label something "high judgment" then leave
   most of it to AI — that is a contradiction and will be rejected.
3. If risk_if_ai_gets_it_wrong = "high", lean toward
   keep_human_pct >= 20 unless you have a specific mitigation in mind.
4. automate_examples / assist_examples / keep_human_examples: SHORT
   sub-tasks. 1-2 items per list, each ≤ 12 words. Each non-zero pct
   requires at least one example.

Output also overall_top_three_ids: the three workflow_ids with ranks 1, 2, 3.

Be specific to the owner. Do not pad. JSON only.
"""


BET_DESIGNER_PROMPT = """\
You are designing ONE 30-day experiment for a small business owner.

Parsed intake (JSON):
{parsed_intake_json}

Leverage analysis (JSON):
{leverage_analysis_json}

Produce a `ThirtyDayBet` against the top-ranked workflow (or one of
the top three if it fits the owner's budgets better):

- target_workflow_id: MUST be one of
  leverage_analysis.overall_top_three_ids.
- title: short.
- hypothesis: "If we test X via Y, we will see <evidence> within 30 days."
- success_metric: observable in 30 days. A measurable change, not a vibe.
- failure_metric: a genuine off-ramp. Must DIFFER in substance from the
  success_metric.
- weekly_plan: EXACTLY 4 entries, one per week (week 1..4).
- first_48h_actions: 2-3 BITE-SIZED actions. The owner only has
  ~2/7 of their weekly_time_budget_hours available within 48 hours
  (a weekend). Each action ≤ 20 minutes of work. Total time across
  all first_48h_actions ≤ 1 hour. Examples of good actions:
  "block 30 min on calendar to draft template", "list current step-
  by-step process from memory", "open 3 vendor sites and bookmark
  pricing". Examples of BAD actions (too big for 48h):
  "research and select a tool", "build prompt template", "set up
  integration".
- expected_asset_created: what the owner has at day 30 regardless of outcome.
- estimated_weekly_time_hours: must be <= parsed_intake.weekly_time_budget_hours.
- estimated_setup_cost_usd: must be <= parsed_intake.monthly_budget_usd.

The bet must be specific to the owner's tools, role, and primary_goal.
"""


RISK_MAPPER_PROMPT = """\
You are mapping risks and human-agency safeguards for a small business
owner's AI rollout. Be terse — each string ≤ 20 words.

Parsed intake (JSON):
{parsed_intake_json}

Workflow map (JSON):
{workflow_map_json}

Leverage analysis (JSON):
{leverage_analysis_json}

Produce a `RiskAndAgencyMap`:

- keep_human_areas: MUST contain at least one entry for EVERY item
  in parsed_intake.refused_automation_areas (substring or clear
  synonym). Optionally add 1-2 extra entries for additional unsafe
  areas the audit identifies. Minimum 2 entries; no upper cap if the
  owner listed many refused items. Fields: area, reason, severity
  (low/medium/high).
- automation_risks: 2-4 entries. Fields: automation, what_could_break,
  mitigation.
- agency_checkpoints: 3-5 entries. Fields: trigger, required_action,
  cadence (per_event/daily/weekly/monthly).
- weekly_review_questions: 3-5 short questions the owner asks each
  week. At least one references each keep_human_area thematically.
- compliance_or_legal_flags: may be an empty list.

JSON only.
"""


PLAYBOOK_BUILDER_PROMPT = """\
You are producing the first version of an operational AI Playbook for
a small business. Be terse — each string ≤ 30 words.

Parsed intake (JSON):
{parsed_intake_json}

Workflow map (JSON):
{workflow_map_json}

Leverage analysis (JSON):
{leverage_analysis_json}

Thirty-day bet (JSON):
{thirty_day_bet_json}

Risk and agency map (JSON):
{risk_and_agency_map_json}

Produce a `FirstPlaybook`:

- title: e.g. "<Business descriptor> — AI Playbook v1".
- business_summary: 2-3 short sentences.
- workflow_entries: EXACTLY one PlaybookEntry per workflow in
  workflow_map.workflows. Fill current_status using this two-step
  procedure — DO NOT skip step 1.

  STEP 1 (mandatory, do this FIRST):
      Find the workflow_entry whose workflow_id exactly matches
      thirty_day_bet.target_workflow_id (from the input above).
      Set THAT entry's current_status to "experimenting".

  STEP 2 (after step 1):
      For every other workflow_entry, set current_status to
      "not_yet_tested".

  Exactly ONE entry will be "experimenting" — the one matching the
  bet's target_workflow_id. All others are "not_yet_tested".
  If you produce a playbook where the target's status is not
  "experimenting", you have produced an invalid output.

  Each entry also needs:
    - workflow_id (matches the workflow_map id).
    - summary: 1 short sentence.
- rules_for_human_involvement: 3-5 entries drawn from
  risk_and_agency_map.
- open_questions: 2-4 entries.
- next_review_offset_days: default 30.

JSON only.
"""

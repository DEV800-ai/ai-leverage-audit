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

For each workflow:
- id: lowercase slug, alphanumeric with hyphens, unique within this
  Audit (e.g. "lead-followup", "client-invoicing").
- title: short human-readable label.
- description: 1-2 sentences.
- frequency: one of "daily" / "weekly" / "monthly" / "event_driven".
- minutes_per_occurrence and occurrences_per_week: integers.
- inputs: what triggers the workflow.
- outputs: what it produces.
- pain_points: list of strings tied to this workflow specifically.
- tools_used: tools currently used for this workflow; subset of
  parsed_intake.tools_in_use.

Cluster related weekly_tasks into workflows. Aim for 3-6 workflows
for a typical solo or small-team owner.
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

Mix fields:
- automate_pct + assist_pct + keep_human_pct must sum to EXACTLY 100.
- For human_judgment_needed = "high", keep_human_pct must be >= 30.
- automate_examples / assist_examples / keep_human_examples: SHORT
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
- first_48h_actions: at least 2 actions completable in 48 hours.
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

- keep_human_areas: 2-4 entries. Areas where automation is unsafe.
  Each entry MUST cover every item from
  parsed_intake.refused_automation_areas (substring or clear synonym).
  Fields: area, reason, severity (low/medium/high).
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
  workflow_map.workflows. For each:
    - workflow_id (matches the workflow_map id).
    - current_status: MUST follow these rules without exception:
        * If workflow_id == thirty_day_bet.target_workflow_id
          → "experimenting" (this is mandatory; do not pick anything else).
        * Else if workflow_id NOT in
          leverage_analysis.overall_top_three_ids
          → "not_yet_tested".
        * Else (other top-3 workflows)
          → "not_yet_tested".
    - summary: 1 short sentence.
- rules_for_human_involvement: 3-5 entries drawn from
  risk_and_agency_map.
- open_questions: 2-4 entries.
- next_review_offset_days: default 30.

JSON only.
"""

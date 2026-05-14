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
- refused_automation_areas: extract from
  things_owner_refuses_to_automate_text. May be empty list.

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
You are scoring AI leverage for each workflow in a small business.

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
- rank: 1 = highest leverage. Assign UNIQUE ranks 1..N across all
  workflows (a permutation, no duplicates).
- rationale: 1-3 sentences specific to this business.

Mix fields:
- automate_pct + assist_pct + keep_human_pct must sum to EXACTLY 100.
- For human_judgment_needed = "high", keep_human_pct must be >= 30.
- automate_examples / assist_examples / keep_human_examples: concrete
  sub-tasks. Each non-zero pct requires at least one example.

Output also overall_top_three_ids: the three workflow_ids with ranks 1, 2, 3.
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
owner's AI rollout.

Parsed intake (JSON):
{parsed_intake_json}

Workflow map (JSON):
{workflow_map_json}

Leverage analysis (JSON):
{leverage_analysis_json}

Produce a `RiskAndAgencyMap`:

- keep_human_areas: at LEAST 2. Areas where automation is unsafe:
  regulated work, customer-trust, high-judgment work. Each entry must
  include every item from parsed_intake.refused_automation_areas
  (matched by substring or clear synonym). Each entry has area /
  reason / severity.
- automation_risks: at LEAST 2. For each: automation,
  what_could_break, mitigation.
- agency_checkpoints: at LEAST 3. For each: trigger, required_action,
  cadence.
- weekly_review_questions: 3-6 questions the owner asks themselves
  each week. At least one question should reference each
  keep_human_area thematically.
- compliance_or_legal_flags: may be an empty list.
"""


PLAYBOOK_BUILDER_PROMPT = """\
You are producing the first version of an operational AI Playbook for
a small business.

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
- business_summary: 2-3 sentences synthesising the business.
- workflow_entries: EXACTLY one PlaybookEntry per workflow in
  workflow_map.workflows. For each:
    - workflow_id (matches the workflow_map id).
    - current_status: "experimenting" for the bet's target_workflow_id.
      "not_yet_tested" for workflows NOT in
      leverage_analysis.overall_top_three_ids. For other top-3
      workflows pick "not_yet_tested" or "experimenting" by bet relevance.
    - summary: 1-2 sentences.
- rules_for_human_involvement: at LEAST 3, drawn from
  risk_and_agency_map's keep_human_areas and agency_checkpoints.
- open_questions: things V1 cannot answer for this business.
- next_review_offset_days: default 30.
"""

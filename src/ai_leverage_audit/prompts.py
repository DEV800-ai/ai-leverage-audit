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
- baseline_measurements: extract from measurement_context_text if
  present. Produce one BaselineMeasurement entry per task the owner
  measured. For each entry:
    - task_or_workflow_ref: the task name the owner described.
    - volume_per_week: number of units per week (float), or null.
    - minutes_per_unit: time per unit in minutes (float), or null.
    - mechanical_pct: integer 0-100, or null.
    - error_rate_1_in_x: e.g. "1 in 20" → 20.0, or null.
    - minutes_to_fix_error: float, or null.
    - owner_review_pct_if_assisted: integer 0-100; convert "every
      single one" → 100, "spot-check 1 in 5" → 20, or null.
    - owner_success_description: owner's free-text "worked" answer,
      or null.
    - owner_stop_condition: owner's free-text stop condition, or null.
  If measurement_context_text is absent or empty, return [].

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

{prior_playbook_section}
{healthcare_section}
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

MINIMALITY RULE (mandatory):
Owners consistently report that bets covering an entire workflow are
too ambitious for 30 days. Target ONE NARROW SLICE of the chosen
workflow — not the whole workflow.

If the workflow is "Lead management" (with sub-activities: intake
messages, qualification, scheduling, follow-up), pick EXACTLY ONE
sub-activity for the 30-day bet. The other sub-activities stay
untouched until a future cycle.

The hypothesis, success_metric, and first_48h_actions must all
reference this single sub-activity by name. Do NOT mix multiple
sub-activities into one bet.

Examples of properly-narrow bets (good):
- "Automate the first reply to inbound WhatsApp lead inquiries"
  (NOT "automate lead management")
- "Draft initial proposal templates for fixed-fee engagements"
  (NOT "automate the entire proposal workflow")
- "Send appointment reminders 24h before visits"
  (NOT "automate patient communication")

Examples of bets that are too broad (bad):
- "Automate appointment scheduling, reminders, and follow-ups"
  (three sub-activities — pick one)
- "Streamline content creation and social distribution"
  (two sub-activities — pick one)

Then complete:

- target_workflow_id: MUST be one of
  leverage_analysis.overall_top_three_ids.
- title: short, referencing the ONE sub-activity.
- hypothesis: "If we test X via Y, we will see <evidence> within 30 days."
- success_metric: observable in 30 days. A measurable change, not a vibe.
  BASELINE RULE: if parsed_intake.baseline_measurements contains an entry
  whose task_or_workflow_ref matches the target workflow, you MUST anchor
  the metric to the owner's own numbers. Example: if the owner reported
  30 min/invoice and you target 40% reduction, write "under 18 min/invoice
  (40% reduction from your stated 30 min average)" — not a number you
  invent. If no baseline data exists, state the metric as a relative
  improvement ("reduce by ~40% from your Week 1 measured average") so the
  threshold is set after real measurement, not before.
- failure_metric: a genuine off-ramp. Must DIFFER in substance from the
  success_metric. Apply the same BASELINE RULE — anchor to owner numbers
  when available, or express relative to Week 1 baseline when not.
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

{prior_outcome_section}
{healthcare_section}
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

{healthcare_section}
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
- cycle_number: set to 1 for a first audit. For continuation audits,
  this value is provided in the prior_playbook_section below.

JSON only.

{prior_playbook_section}
"""


# ── Healthcare context sections ─────────────────────────────────────────────
# Injected into the relevant prompts when _is_healthcare() is True.
# All three sections are opt-in: the default variable value is "" (empty).

HEALTHCARE_LEVERAGE_SECTION = """\
HEALTHCARE CONTEXT — apply before scoring, these override default rules:
- Patient-facing or clinical workflows: human_judgment_needed = "high",
  keep_human_pct >= 40, automate_pct <= 20. Use "draft" or "triage"
  language in automate_examples — never "auto-reply" or "auto-send to patient".
- Appointment management: automate_pct <= 25. Every automate example must
  include "requires staff confirmation". Never describe auto-booking.
- Medication or medical-inventory workflows: automate_pct <= 15,
  human_judgment_needed = "high". Never suggest auto-ordering.
- Assist-first default: for every clinical or patient-facing workflow,
  assist_pct >= automate_pct.
- Add "assist-first approach due to healthcare context" to each rationale
  that would otherwise lean toward full automation.
"""

HEALTHCARE_BET_SECTION = """\
HEALTHCARE BET CONSTRAINTS — mandatory:
1. TRIAGE + DRAFT, not auto-reply: every patient-facing action in this bet
   must be reviewed by a human before it reaches any patient. Use language
   like "draft for staff review", "template staff selects from", or
   "route to reception" — not "auto-send" or "auto-reply".
2. No auto-scheduling: if the bet touches appointments at all, a human
   confirmation step is required before any booking is confirmed or changed.
3. No auto-ordering: do not recommend automatic ordering of medication,
   supplies, or any medical inventory.
4. Safety metrics: success_metric MUST include "100% of drafted messages
   reviewed by staff before sending" or equivalent. failure_metric MUST
   include "any automated message reaches a patient without human review
   = immediate stop".
5. PROGRESSION RULE: if the owner's primary_goal involves scheduling or
   clinical follow-ups, choose a lower-risk sub-activity for this bet
   (e.g. WhatsApp/intake triage). Add this sentence to the hypothesis:
   "Scheduling and treatment follow-ups are higher-risk workflows — this
   first 30-day bet starts with lower-risk non-medical intake triage to
   build confidence before advancing."
6. Implementation: expected_asset_created should reference an approved
   template library with human-gated sending — not EHR integration or
   appointment system APIs in cycle 1.
"""

HEALTHCARE_RISK_SECTION = """\
HEALTHCARE RISK CONSTRAINTS — mandatory:
1. keep_human_areas MUST include at minimum:
   - area: "Medical advice, symptom or treatment questions", severity: "high",
     reason: "Only licensed clinicians can advise on clinical matters"
   - area: "Patient health information (PHI) and HIPAA compliance",
     severity: "high", reason: "Patient data requires HIPAA-compliant handling"
2. compliance_or_legal_flags MUST include:
   - "HIPAA: no patient health information (PHI) in automated message templates"
   - "BAA required before sharing any patient data with an AI tool or vendor"
3. weekly_review_questions MUST be specific to the 30-day bet's sub-activity
   (see bet_context below). For a WhatsApp triage or patient-intake bet, use:
   - "How many inbound WhatsApp inquiries arrived this week?"
   - "How many were handled using approved templates (no staff edit needed)?"
   - "How many required escalation to a staff member?"
   - "Did any automated draft touch medical content (symptoms, treatment,
     medication)?"
   - "Did any patient complain about tone or content of a message?"
   - "How much staff time was saved vs. your Week 1 baseline?"
   Do NOT ask about EHR records, billing, or inventory unless that is what
   the 30-day bet targets.
4. automation_risks MUST include:
   - automation: "AI-drafted patient messages",
     what_could_break: "Template used for a medical question it was not designed
     for", mitigation: "All drafts reviewed by staff; medical queries auto-flag
     for escalation and are never sent automatically"
"""

OUTCOME_PARSER_PROMPT = """\
You are converting a small business owner's free-text outcome report into
structured fields after they completed a 30-day AI experiment.

Prior 30-day bet (JSON):
{prior_bet_json}

Owner's free-text outcome:
{outcome_text}

Produce an `OutcomeReport`:

- prior_workflow_run_id: copy from the bet JSON's workflow context if
  present, otherwise use the placeholder UUID provided.
- prior_bet_title: copy the bet's title.
- outcome: classify as "succeeded" / "failed" / "mixed" / "abandoned".
  "succeeded" = success_metric clearly triggered. "failed" = failure
  metric clearly triggered or owner gave up. "mixed" = partial results,
  unclear which metric triggered. "abandoned" = owner stopped before
  week 4 without a clear result.
- success_metric_triggered: true if the owner's text indicates the
  success condition was met, even partially. Err toward false if unclear.
- failure_metric_triggered: true if the owner's text indicates the
  failure condition was met. Err toward false if unclear.
- actual_weekly_hours_invested: estimate from the text. If not stated,
  use the bet's estimated_weekly_time_hours.
- actual_setup_cost_usd: estimate from the text. If not stated, use 0.
- what_worked_text: quote or paraphrase the most positive finding.
  Minimum 30 characters. Must reflect what the owner actually said.
- what_surprised_text: quote or paraphrase the biggest surprise
  (positive or negative). Minimum 30 characters.
- what_owner_would_change_text: quote or paraphrase the owner's
  suggested change. Minimum 30 characters. If not stated, infer
  from context.
- intent: "continue" / "pivot" / "stop". "continue" = same direction.
  "pivot" = different workflow or approach. "stop" = abandon AI here.

Be honest about uncertainty — do not invent specifics the owner did not
state. JSON only.
"""

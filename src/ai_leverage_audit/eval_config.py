"""Eval configuration for the AI Leverage Audit Critic.

Two layers (PRODUCT_MVP.md §5 + §6):
- LEVERAGE_AUDIT_RULES: 10 deterministic cross-artifact rules.
- LEVERAGE_AUDIT_RUBRIC: 6 subjective questions for the LLM judge,
  fired only when all deterministic rules pass.

`AuditState` bundles all six LLM-produced artifacts so the rules can run
as `Rule[AuditState]` against a single value. The platform's rule_eval
primitive operates on one artifact at a time; AuditState is the
cross-artifact unit.
"""

from __future__ import annotations

from leverage_platform.eval import Rule
from pydantic import BaseModel, ConfigDict

from ai_leverage_audit.schemas import (
    FirstPlaybook,
    LeverageAnalysis,
    ParsedIntake,
    RiskAndAgencyMap,
    ThirtyDayBet,
    WorkflowMap,
)


class AuditState(BaseModel):
    """All six LLM-produced artifacts of one Audit, bundled for rule eval."""

    model_config = ConfigDict(extra="forbid")

    parsed_intake: ParsedIntake
    workflow_map: WorkflowMap
    leverage_analysis: LeverageAnalysis
    thirty_day_bet: ThirtyDayBet
    risk_and_agency_map: RiskAndAgencyMap
    first_playbook: FirstPlaybook


# ---------- Rule checks ----------


def _all_workflows_have_leverage_entry(state: AuditState) -> tuple[bool, str]:
    workflow_ids = {w.id for w in state.workflow_map.workflows}
    leverage_ids = {wl.workflow_id for wl in state.leverage_analysis.per_workflow}
    if workflow_ids != leverage_ids:
        missing = workflow_ids - leverage_ids
        extra = leverage_ids - workflow_ids
        return False, (
            f"workflow_ids mismatch — missing in leverage: {sorted(missing)}, "
            f"extra in leverage: {sorted(extra)}"
        )
    return True, "every workflow has exactly one leverage entry"


def _bet_target_in_top_three(state: AuditState) -> tuple[bool, str]:
    target = state.thirty_day_bet.target_workflow_id
    if target not in state.leverage_analysis.overall_top_three_ids:
        return False, (
            f"bet target {target!r} not in overall_top_three_ids "
            f"{state.leverage_analysis.overall_top_three_ids}"
        )
    return True, f"bet target {target!r} is in top three"


def _bet_time_within_intake(state: AuditState) -> tuple[bool, str]:
    bet_h = state.thirty_day_bet.estimated_weekly_time_hours
    budget_h = state.parsed_intake.weekly_time_budget_hours
    if bet_h > budget_h:
        return False, f"bet weekly time {bet_h}h exceeds intake budget {budget_h}h"
    return True, f"bet weekly time {bet_h}h within budget {budget_h}h"


def _bet_cost_within_intake(state: AuditState) -> tuple[bool, str]:
    bet_c = state.thirty_day_bet.estimated_setup_cost_usd
    budget_c = state.parsed_intake.monthly_budget_usd
    if bet_c > budget_c:
        return False, f"bet setup cost ${bet_c} exceeds intake budget ${budget_c}"
    return True, f"bet setup cost ${bet_c} within budget ${budget_c}"


def _percentages_sum_per_workflow(state: AuditState) -> tuple[bool, str]:
    for wl in state.leverage_analysis.per_workflow:
        total = wl.automate_pct + wl.assist_pct + wl.keep_human_pct
        if total != 100:
            return False, f"workflow {wl.workflow_id!r}: pcts sum to {total}, not 100"
    return True, "all workflow pcts sum to 100"


def _playbook_entries_match_workflow_count(state: AuditState) -> tuple[bool, str]:
    n_workflows = len(state.workflow_map.workflows)
    n_entries = len(state.first_playbook.workflow_entries)
    if n_entries != n_workflows:
        return False, (
            f"playbook entries ({n_entries}) != workflow count ({n_workflows})"
        )
    return True, f"playbook has one entry per workflow ({n_workflows})"


def _target_workflow_is_experimenting(state: AuditState) -> tuple[bool, str]:
    target = state.thirty_day_bet.target_workflow_id
    for entry in state.first_playbook.workflow_entries:
        if entry.workflow_id == target:
            if entry.current_status != "experimenting":
                return False, (
                    f"target workflow {target!r} has status "
                    f"{entry.current_status!r}, expected 'experimenting'"
                )
            return True, f"target workflow {target!r} is experimenting"
    return False, f"target workflow {target!r} not found in playbook entries"


def _refused_areas_reflected_in_keep_human(state: AuditState) -> tuple[bool, str]:
    refused = [r.strip().lower() for r in state.parsed_intake.refused_automation_areas if r.strip()]
    if not refused:
        return True, "no refused areas to check"
    keep_human_text = " ".join(
        f"{kh.area} {kh.reason}".lower()
        for kh in state.risk_and_agency_map.keep_human_areas
    )
    # Substring check; the LLM judge handles synonym recognition.
    missing = [r for r in refused if r not in keep_human_text]
    if missing:
        return False, (
            f"refused areas not reflected (substring match) in keep_human_areas: {missing}"
        )
    return True, "all refused areas reflected in keep_human_areas"


def _high_judgment_keep_human_at_least_30(state: AuditState) -> tuple[bool, str]:
    violators = [
        f"{wl.workflow_id} (keep_human={wl.keep_human_pct}%)"
        for wl in state.leverage_analysis.per_workflow
        if wl.human_judgment_needed == "high" and wl.keep_human_pct < 30
    ]
    if violators:
        return False, f"high-judgment workflows below 30% keep_human: {violators}"
    return True, "all high-judgment workflows have keep_human ≥ 30%"


def _failure_not_identical_to_success(state: AuditState) -> tuple[bool, str]:
    s = state.thirty_day_bet.success_metric.strip().lower()
    f = state.thirty_day_bet.failure_metric.strip().lower()
    if s == f:
        return False, "failure_metric is identical to success_metric (case/space-insensitive)"
    return True, "failure_metric differs from success_metric"


LEVERAGE_AUDIT_RULES: list[Rule[AuditState]] = [
    Rule(
        name="all_workflows_have_leverage_entry",
        check=_all_workflows_have_leverage_entry,
    ),
    Rule(name="bet_target_in_top_three", check=_bet_target_in_top_three),
    Rule(name="bet_time_within_intake", check=_bet_time_within_intake),
    Rule(name="bet_cost_within_intake", check=_bet_cost_within_intake),
    Rule(name="percentages_sum_per_workflow", check=_percentages_sum_per_workflow),
    Rule(
        name="playbook_entries_match_workflow_count",
        check=_playbook_entries_match_workflow_count,
    ),
    Rule(
        name="target_workflow_is_experimenting",
        check=_target_workflow_is_experimenting,
    ),
    Rule(
        name="refused_areas_reflected_in_keep_human",
        check=_refused_areas_reflected_in_keep_human,
    ),
    Rule(
        name="high_judgment_keep_human_at_least_30",
        check=_high_judgment_keep_human_at_least_30,
    ),
    Rule(
        name="failure_not_identical_to_success",
        check=_failure_not_identical_to_success,
    ),
]


LEVERAGE_AUDIT_RUBRIC: list[str] = [
    "Is each workflow in WorkflowMap genuinely a recurring pattern, not a one-off task?",
    (
        "Are LeverageAnalysis.rationale entries specific to the owner's actual "
        "business, not generic advice?"
    ),
    (
        "Does ThirtyDayBet.first_48h_actions realistically fit in 48 hours given "
        "the owner's stated weekly time budget?"
    ),
    (
        "Is ThirtyDayBet.failure_metric a genuine off-ramp (observable, decisive) "
        "rather than a face-saver?"
    ),
    (
        "Do the RiskAndAgencyMap.keep_human_areas reflect actual customer-trust / "
        "regulated / judgment-heavy work, rather than just things the owner finds "
        "tedious?"
    ),
    (
        "Does FirstPlaybook produce a compounding asset (knowledge, validated "
        "workflow, customer relationship) rather than just a saved-time list?"
    ),
]

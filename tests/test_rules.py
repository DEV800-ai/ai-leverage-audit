"""Deterministic rule tests — PRODUCT_MVP.md §5.

Each rule gets a happy-path test (passes on the factory's AuditState)
and a failing-mutation test (mutate one part of the state to break that
specific rule and confirm it fires).
"""

from __future__ import annotations

import pytest
from leverage_platform.eval import rule_eval

from ai_leverage_audit.eval_config import (
    CONTINUATION_AUDIT_RULES,
    LEVERAGE_AUDIT_RULES,
    AuditState,
    ContinuationAuditState,
)
from ai_leverage_audit.schemas import (
    AuditIntake,
    OutcomeReport,
    PlaybookEntry,
    Workflow,
)
from tests.conftest import (
    _bet_for,
    _leverage_analysis_for,
    _outcome_report_for,
    _parsed_intake_for,
    _playbook_for,
    _risk_and_agency_map_for,
    _workflow_map_for,
    _continuation_playbook_for,
)


@pytest.fixture
def state(intake: AuditIntake) -> AuditState:
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    bet = _bet_for(parsed, leverage)
    risk_map = _risk_and_agency_map_for(parsed)
    playbook = _playbook_for(workflow_map, leverage, bet)
    return AuditState(
        parsed_intake=parsed,
        workflow_map=workflow_map,
        leverage_analysis=leverage,
        thirty_day_bet=bet,
        risk_and_agency_map=risk_map,
        first_playbook=playbook,
    )


def test_all_rules_pass_on_factory_state(state: AuditState) -> None:
    """The conftest factory must produce a state that satisfies every rule."""
    report = rule_eval(state, LEVERAGE_AUDIT_RULES)
    assert report.accepted is True, f"unexpected rule failures: {report.summary}"
    assert all(c.passed for c in report.criteria)


def test_bet_target_outside_top_three_fails(state: AuditState) -> None:
    # Pick a workflow not in top three and use it as target.
    top_three = set(state.leverage_analysis.overall_top_three_ids)
    outside = next(
        w.id for w in state.workflow_map.workflows if w.id not in top_three
    )
    mutated = state.model_copy(
        update={
            "thirty_day_bet": state.thirty_day_bet.model_copy(
                update={"target_workflow_id": outside}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "bet_target_in_top_three" in fails


def test_bet_time_over_budget_fails(state: AuditState) -> None:
    over_budget = state.parsed_intake.weekly_time_budget_hours + 5
    mutated = state.model_copy(
        update={
            "thirty_day_bet": state.thirty_day_bet.model_copy(
                update={"estimated_weekly_time_hours": over_budget}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "bet_time_within_intake" in fails


def test_bet_cost_over_budget_fails(state: AuditState) -> None:
    over_budget = state.parsed_intake.monthly_budget_usd + 50
    mutated = state.model_copy(
        update={
            "thirty_day_bet": state.thirty_day_bet.model_copy(
                update={"estimated_setup_cost_usd": over_budget}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "bet_cost_within_intake" in fails


def test_workflow_count_mismatch_in_playbook_fails(state: AuditState) -> None:
    # Drop one entry to break rule 6.
    truncated_entries = state.first_playbook.workflow_entries[:-1]
    mutated = state.model_copy(
        update={
            "first_playbook": state.first_playbook.model_copy(
                update={"workflow_entries": truncated_entries}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "playbook_entries_match_workflow_count" in fails


def test_target_workflow_not_experimenting_fails(state: AuditState) -> None:
    target = state.thirty_day_bet.target_workflow_id
    new_entries = [
        PlaybookEntry(
            workflow_id=entry.workflow_id,
            current_status=(
                "not_yet_tested" if entry.workflow_id == target else entry.current_status
            ),
            summary=entry.summary,
        )
        for entry in state.first_playbook.workflow_entries
    ]
    mutated = state.model_copy(
        update={
            "first_playbook": state.first_playbook.model_copy(
                update={"workflow_entries": new_entries}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "target_workflow_is_experimenting" in fails


def test_refused_area_missing_from_keep_human_fails(state: AuditState) -> None:
    # Replace keep_human_areas with ones that don't mention the refused area.
    new_keep_human = [
        kh.model_copy(update={"area": "Unrelated area", "reason": "no overlap"})
        for kh in state.risk_and_agency_map.keep_human_areas
    ]
    mutated = state.model_copy(
        update={
            "risk_and_agency_map": state.risk_and_agency_map.model_copy(
                update={"keep_human_areas": new_keep_human}
            )
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    if state.parsed_intake.refused_automation_areas:
        assert report.accepted is False
        fails = [c.name for c in report.criteria if not c.passed]
        assert "refused_areas_reflected_in_keep_human" in fails


def test_rejected_workflow_not_retargeted_passes(
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """No rejected workflows in prior playbook → rule passes."""
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    bet = _bet_for(parsed, leverage)
    risk_map = _risk_and_agency_map_for(parsed)
    prior_playbook = _playbook_for(workflow_map, leverage, bet)
    # Cycle 2 targets rank-2 workflow.
    rank2_id = next(w.workflow_id for w in leverage.per_workflow if w.rank == 2)
    bet2 = bet.model_copy(update={"target_workflow_id": rank2_id})
    playbook2 = _continuation_playbook_for(
        workflow_map, leverage, bet2, bet.target_workflow_id, "succeeded"
    )
    cont_state = ContinuationAuditState(
        parsed_intake=parsed,
        workflow_map=workflow_map,
        leverage_analysis=leverage,
        thirty_day_bet=bet2,
        risk_and_agency_map=risk_map,
        first_playbook=playbook2,
        outcome_report=outcome_report,
        prior_playbook=prior_playbook,
    )
    report = rule_eval(cont_state, CONTINUATION_AUDIT_RULES)
    assert report.accepted is True


def test_rejected_workflow_retargeted_fails(
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """Targeting a rejected workflow → rule fires."""
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    bet = _bet_for(parsed, leverage)
    risk_map = _risk_and_agency_map_for(parsed)
    prior_target = bet.target_workflow_id
    # Mark prior target as rejected in prior playbook.
    prior_playbook = _playbook_for(workflow_map, leverage, bet)
    rejected_entries = [
        e.model_copy(update={"current_status": "rejected"})
        if e.workflow_id == prior_target
        else e
        for e in prior_playbook.workflow_entries
    ]
    prior_playbook = prior_playbook.model_copy(update={"workflow_entries": rejected_entries})
    # Attempt to retarget the same (now rejected) workflow.
    playbook2 = _continuation_playbook_for(
        workflow_map, leverage, bet, prior_target, "failed"
    )
    cont_state = ContinuationAuditState(
        parsed_intake=parsed,
        workflow_map=workflow_map,
        leverage_analysis=leverage,
        thirty_day_bet=bet,  # still targets prior_target
        risk_and_agency_map=risk_map,
        first_playbook=playbook2,
        outcome_report=outcome_report,
        prior_playbook=prior_playbook,
    )
    report = rule_eval(cont_state, CONTINUATION_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "rejected_workflow_not_retargeted" in fails


def test_workflows_and_leverage_mismatch_fails(state: AuditState) -> None:
    # Add an extra workflow but no leverage entry for it — rule 1 fires.
    extra = Workflow(
        id="extra-workflow",
        title="Extra",
        description="Added to break the mapping.",
        frequency="weekly",
        minutes_per_occurrence=10,
        occurrences_per_week=1,
        inputs="n/a",
        outputs="n/a",
        pain_points=[],
        tools_used=[],
    )
    # WorkflowMap allows up to 8; conftest factory makes 5 — adding one is fine.
    new_workflows = [*state.workflow_map.workflows, extra]
    new_entries = [
        *state.first_playbook.workflow_entries,
        PlaybookEntry(
            workflow_id=extra.id,
            current_status="not_yet_tested",
            summary="extra entry to keep counts matching",
        ),
    ]
    mutated = state.model_copy(
        update={
            "workflow_map": state.workflow_map.model_copy(
                update={"workflows": new_workflows}
            ),
            "first_playbook": state.first_playbook.model_copy(
                update={"workflow_entries": new_entries}
            ),
        }
    )
    report = rule_eval(mutated, LEVERAGE_AUDIT_RULES)
    assert report.accepted is False
    fails = [c.name for c in report.criteria if not c.passed]
    assert "all_workflows_have_leverage_entry" in fails

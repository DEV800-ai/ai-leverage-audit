"""Test fixtures for the AI Leverage Audit.

Provides:
- `store`: in-memory SQLiteStore per test.
- `intake`: loads fixtures/intakes/synthetic_consultant.json into an AuditIntake.
- `ctx`: AgentContext wired with a MockLLMProvider whose multi-schema
  factory produces rule-passing outputs for the loaded intake.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from uuid import UUID

import pytest
from leverage_platform.llm import MockLLMProvider
from leverage_platform.runtime import AgentContext
from leverage_platform.schemas import EvalCriterion, EvalReport
from leverage_platform.storage import SQLiteStore
from pydantic import BaseModel

from ai_leverage_audit.eval_config import LEVERAGE_AUDIT_RUBRIC
from ai_leverage_audit.schemas import (
    AgencyCheckpoint,
    AuditIntake,
    AutomationRisk,
    FirstPlaybook,
    KeepHumanArea,
    LeverageAnalysis,
    OutcomeReport,
    ParsedIntake,
    PlaybookEntry,
    RiskAndAgencyMap,
    ThirtyDayBet,
    WeeklyTask,
    Workflow,
    WorkflowLeverage,
    WorkflowMap,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "intakes"
OUTCOMES_DIR = Path(__file__).parent.parent / "fixtures" / "outcomes"


# ---------- Factory functions producing rule-passing artifacts ----------


def _parsed_intake_for(intake: AuditIntake) -> ParsedIntake:
    return ParsedIntake(
        business_summary=(
            f"A {intake.team_size}-person {intake.business_type} run by an "
            f"{intake.current_role}."
        ),
        weekly_tasks=[
            WeeklyTask(
                title="Lead discovery and qualification",
                estimated_time_minutes_per_week=180,
                is_customer_facing=True,
                is_error_sensitive=True,
                current_tool="Calendly",
            ),
            WeeklyTask(
                title="Proposal writing",
                estimated_time_minutes_per_week=150,
                is_customer_facing=True,
                is_error_sensitive=True,
                current_tool="Notion",
            ),
            WeeklyTask(
                title="Client project updates",
                estimated_time_minutes_per_week=120,
                is_customer_facing=True,
                is_error_sensitive=False,
                current_tool="Loom",
            ),
            WeeklyTask(
                title="Invoicing and follow-up",
                estimated_time_minutes_per_week=60,
                is_customer_facing=True,
                is_error_sensitive=True,
                current_tool="Stripe",
            ),
            WeeklyTask(
                title="Content publication",
                estimated_time_minutes_per_week=180,
                is_customer_facing=True,
                is_error_sensitive=False,
                current_tool="ConvertKit",
            ),
        ],
        tools_in_use=["Notion", "Stripe", "Figma", "ConvertKit", "LinkedIn", "Gmail"],
        top_pain_points=[
            "Proposal writing takes hours of repeated work",
            "Stale lead follow-ups get forgotten",
            "Client weekly status updates feel repetitive",
        ],
        primary_goal=intake.primary_goal_text,
        weekly_time_budget_hours=intake.weekly_time_to_invest_hours,
        monthly_budget_usd=intake.monthly_budget_usd,
        refused_automation_areas=(
            ["Direct client communication"]
            if intake.things_owner_refuses_to_automate_text
            else []
        ),
    )


def _workflow_map_for(_parsed: ParsedIntake) -> WorkflowMap:
    return WorkflowMap(
        workflows=[
            Workflow(
                id="lead-qualification",
                title="Lead qualification and discovery",
                description="Booking discovery calls and qualifying new leads.",
                frequency="weekly",
                minutes_per_occurrence=60,
                occurrences_per_week=3,
                inputs="Inbound inquiries via LinkedIn / referrals",
                outputs="Qualified-lead notes and a follow-up action",
                pain_points=["Forgetting to follow up on stale leads"],
                tools_used=["Calendly", "Gmail", "Notion"],
            ),
            Workflow(
                id="proposal-writing",
                title="Proposal writing",
                description="Composing scoped proposals from discovery notes.",
                frequency="weekly",
                minutes_per_occurrence=150,
                occurrences_per_week=1,
                inputs="Qualified-lead notes",
                outputs="Sent proposal document",
                pain_points=["Each proposal recreates similar structure from scratch"],
                tools_used=["Notion", "Gmail"],
            ),
            Workflow(
                id="client-updates",
                title="Client project status updates",
                description="Weekly project updates to active clients.",
                frequency="weekly",
                minutes_per_occurrence=20,
                occurrences_per_week=5,
                inputs="Project board state",
                outputs="Sent status update message",
                pain_points=["Repetitive shape every week"],
                tools_used=["Notion", "Loom", "Gmail"],
            ),
            Workflow(
                id="invoicing",
                title="Monthly invoicing",
                description="Sending invoices and chasing late payments.",
                frequency="monthly",
                minutes_per_occurrence=45,
                occurrences_per_week=1,
                inputs="Time and deliverable records",
                outputs="Sent invoice, paid invoice",
                pain_points=["Manual reminders for late payers"],
                tools_used=["Stripe", "Gmail"],
            ),
            Workflow(
                id="content-distribution",
                title="Weekly content distribution",
                description="Newsletter draft + scheduled LinkedIn posts.",
                frequency="weekly",
                minutes_per_occurrence=120,
                occurrences_per_week=1,
                inputs="Topic ideas from the week",
                outputs="Sent newsletter and 2 LinkedIn posts",
                pain_points=["Repurposing the same idea across channels is manual"],
                tools_used=["ConvertKit", "LinkedIn"],
            ),
        ]
    )


def _leverage_analysis_for(workflow_map: WorkflowMap) -> LeverageAnalysis:
    """Rank the 5 workflows; top 3 ids must match overall_top_three_ids."""
    per: list[WorkflowLeverage] = []
    # We rank deterministically by workflow id order for the factory.
    rankings = {
        "proposal-writing": 1,
        "lead-qualification": 2,
        "client-updates": 3,
        "content-distribution": 4,
        "invoicing": 5,
    }
    judgments = {
        "proposal-writing": ("medium", "medium", "medium", 60, 30, 10),
        "lead-qualification": ("low", "low", "medium", 50, 40, 10),
        "client-updates": ("low", "low", "low", 70, 20, 10),
        "content-distribution": ("low", "low", "medium", 60, 30, 10),
        "invoicing": ("medium", "low", "high", 40, 30, 30),
    }
    for wf in workflow_map.workflows:
        risk, complexity, judgment, automate, assist, keep = judgments[wf.id]
        per.append(
            WorkflowLeverage(
                workflow_id=wf.id,
                time_saved_hours_per_week_estimate=2.0,
                risk_if_ai_gets_it_wrong=risk,  # type: ignore[arg-type]
                setup_complexity=complexity,  # type: ignore[arg-type]
                human_judgment_needed=judgment,  # type: ignore[arg-type]
                rank=rankings[wf.id],
                rationale=f"AI can help with {wf.title} for this owner specifically.",
                automate_pct=automate,
                assist_pct=assist,
                keep_human_pct=keep,
                automate_examples=[f"Draft the {wf.title.lower()} template"],
                assist_examples=[f"Suggest improvements to {wf.title.lower()}"],
                keep_human_examples=[f"Owner reviews each {wf.title.lower()} output"],
                confidence="medium",
                evidence_from_intake=[
                    f"Intake lists '{wf.title.lower()}' among weekly recurring tasks."
                ],
                assumptions=[
                    "Volume estimated from the intake's pain-point list, not measured."
                ],
            )
        )
    top_three = [wid for wid, r in rankings.items() if r <= 3]
    return LeverageAnalysis(per_workflow=per, overall_top_three_ids=top_three)


def _bet_for(parsed: ParsedIntake, leverage: LeverageAnalysis) -> ThirtyDayBet:
    target = leverage.overall_top_three_ids[0]
    return ThirtyDayBet(
        target_workflow_id=target,
        title=f"AI-drafted {target} bet",
        hypothesis=(
            f"If we test AI-drafted {target} via a structured template, we will "
            "see at least 50 percent reduction in time per occurrence within 30 days."
        ),
        success_metric=(
            "Time per occurrence drops from baseline to ≤ 50% in week 4."
        ),
        failure_metric=(
            "No measurable time saving after 4 weeks or owner edits >75% of each draft."
        ),
        weekly_plan=[
            "Week 1: Define template, draft prompt, baseline current time.",
            "Week 2: Run AI drafts on 3 real cases, owner reviews and edits.",
            "Week 3: Iterate template based on what owner edited the most.",
            "Week 4: Measure final time per occurrence and decide go/pivot/stop.",
        ],
        first_48h_actions=[
            "Write down current time spent per occurrence (baseline).",
            "Draft an initial AI prompt template based on the last 3 cases.",
        ],
        expected_asset_created=(
            "A validated AI prompt template plus baseline + post-intervention "
            "time metric for this workflow."
        ),
        estimated_weekly_time_hours=min(parsed.weekly_time_budget_hours, 4),
        estimated_setup_cost_usd=min(parsed.monthly_budget_usd, 40),
    )


def _risk_and_agency_map_for(parsed: ParsedIntake) -> RiskAndAgencyMap:
    # Compose keep_human_areas so the substring rule matches refused areas.
    refused = parsed.refused_automation_areas or ["Customer trust"]
    keep_human = [
        KeepHumanArea(
            area=refused[0],
            reason=(
                f"{refused[0].lower()} is load-bearing for trust; "
                "owner must remain the final voice."
            ),
            severity="high",
        ),
        KeepHumanArea(
            area="Pricing negotiations and exceptions",
            reason="Pricing decisions encode strategy; AI mishaps damage margins.",
            severity="medium",
        ),
    ]
    return RiskAndAgencyMap(
        keep_human_areas=keep_human,
        automation_risks=[
            AutomationRisk(
                automation="Auto-sending drafted client messages",
                what_could_break="A confidently-wrong message damages a client relationship.",
                mitigation="AI drafts only; owner sends the final.",
            ),
            AutomationRisk(
                automation="Auto-sending invoices without review",
                what_could_break="Wrong amount or wrong client billed.",
                mitigation="Owner reviews every invoice before send.",
            ),
        ],
        agency_checkpoints=[
            AgencyCheckpoint(
                trigger="Any AI-drafted message to a client",
                required_action="Owner reads, edits if needed, and sends.",
                cadence="per_event",
            ),
            AgencyCheckpoint(
                trigger="End of week",
                required_action="Owner reviews AI-handled work for surprises.",
                cadence="weekly",
            ),
            AgencyCheckpoint(
                trigger="A client complains about an AI-assisted output",
                required_action="Pause that workflow's AI assist and review root cause.",
                cadence="per_event",
            ),
        ],
        weekly_review_questions=[
            f"Did anything go out under my name that I would not have sent ({refused[0].lower()})?",
            "Where did AI save me time without hurting quality?",
            "Did I edit the AI draft so heavily it would have been faster to write from scratch?",
        ],
        compliance_or_legal_flags=[],
    )


def _playbook_for(
    workflow_map: WorkflowMap, leverage: LeverageAnalysis, bet: ThirtyDayBet
) -> FirstPlaybook:
    top_three = set(leverage.overall_top_three_ids)
    entries: list[PlaybookEntry] = []
    for wf in workflow_map.workflows:
        if wf.id == bet.target_workflow_id:
            status = "experimenting"
        elif wf.id not in top_three:
            status = "not_yet_tested"
        else:
            status = "not_yet_tested"
        entries.append(
            PlaybookEntry(
                workflow_id=wf.id,
                current_status=status,  # type: ignore[arg-type]
                summary=f"Playbook entry for {wf.title}.",
            )
        )
    return FirstPlaybook(
        title="Branding Consultancy — AI Playbook v1",
        business_summary=(
            "A one-person branding consultancy serving early-stage SaaS clients; "
            "AI is being introduced for high-leverage repetitive work while client "
            "trust touchpoints remain owner-controlled."
        ),
        workflow_entries=entries,
        rules_for_human_involvement=[
            "Owner sends all final client messages.",
            "Owner reviews and approves every invoice before send.",
            "If a client expresses concern about an AI-assisted output, pause and re-evaluate.",
        ],
        open_questions=[
            "How often will the owner update this playbook?",
            "What baseline metrics should be captured for re-eval at 90 days?",
        ],
        next_review_offset_days=30,
    )


def _outcome_report_for(prior_workflow_run_id: UUID) -> OutcomeReport:
    """Synthetic cycle-1 outcome: proposal-writing succeeded, intent=continue."""
    return OutcomeReport(
        prior_workflow_run_id=prior_workflow_run_id,
        prior_bet_title="AI-drafted proposal-writing bet",
        outcome="succeeded",
        success_metric_triggered=True,
        failure_metric_triggered=False,
        actual_weekly_hours_invested=3.5,
        actual_setup_cost_usd=30,
        what_worked_text=(
            "The AI-drafted proposal template reduced writing time from 2.5h to under 45min."
        ),
        what_surprised_text=(
            "Clients expected more personalization — the opening paragraph always needs hand-editing."
        ),
        what_owner_would_change_text=(
            "Add a personalization checklist after the template to avoid forgetting key customizations."
        ),
        intent="continue",
    )


def _continuation_playbook_for(
    workflow_map: WorkflowMap,
    leverage: LeverageAnalysis,
    bet: ThirtyDayBet,
    prior_target: str,
    prior_outcome: str,
) -> FirstPlaybook:
    """Cycle-2 playbook: prior_target status evolved from outcome, new bet is experimenting."""
    status_map = {
        "succeeded": "validated",
        "failed": "rejected",
        "mixed": "experimenting",
        "abandoned": "not_yet_tested",
    }
    prior_resolved = status_map.get(prior_outcome, "not_yet_tested")
    entries: list[PlaybookEntry] = []
    for wf in workflow_map.workflows:
        if wf.id == bet.target_workflow_id:
            status = "experimenting"
            last_summary = None
        elif wf.id == prior_target:
            status = prior_resolved
            last_summary = f"Cycle 1 outcome: {prior_outcome}."
        else:
            status = "not_yet_tested"
            last_summary = None
        entries.append(
            PlaybookEntry(
                workflow_id=wf.id,
                current_status=status,  # type: ignore[arg-type]
                summary=f"Playbook entry for {wf.title}.",
                cycle_introduced=1,
                last_outcome_summary=last_summary,
            )
        )
    return FirstPlaybook(
        title="Branding Consultancy — AI Playbook v2",
        business_summary=(
            "A one-person branding consultancy. Proposal writing validated in cycle 1. "
            "Cycle 2 targets lead qualification."
        ),
        workflow_entries=entries,
        rules_for_human_involvement=[
            "Owner sends all final client messages.",
            "Owner reviews and approves every invoice before send.",
            "If a client expresses concern about an AI-assisted output, pause and re-evaluate.",
        ],
        open_questions=[
            "How often will the owner update this playbook?",
            "What baseline metrics should be captured for re-eval at 90 days?",
        ],
        next_review_offset_days=30,
        cycle_number=2,
    )


def _accepted_eval_report() -> EvalReport:
    return EvalReport(
        accepted=True,
        criteria=[
            EvalCriterion(name=q, passed=True, reason="judged acceptable")
            for q in LEVERAGE_AUDIT_RUBRIC
        ],
        summary="all rubric questions judged acceptable",
    )


# ---------- Factory binding ----------


def _make_factory(
    intake: AuditIntake,
) -> Callable[[type[BaseModel], str], BaseModel]:
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    bet = _bet_for(parsed, leverage)
    risk_map = _risk_and_agency_map_for(parsed)
    playbook = _playbook_for(workflow_map, leverage, bet)
    accepted = _accepted_eval_report()

    def factory(schema: type[BaseModel], prompt: str) -> BaseModel:
        if schema is ParsedIntake:
            return parsed
        if schema is WorkflowMap:
            return workflow_map
        if schema is LeverageAnalysis:
            return leverage
        if schema is ThirtyDayBet:
            return bet
        if schema is RiskAndAgencyMap:
            return risk_map
        if schema is FirstPlaybook:
            return playbook
        if schema is EvalReport:
            return accepted
        raise TypeError(f"No factory branch for {schema.__name__}")

    return factory


def _make_continuation_factory(
    intake: AuditIntake,
    prior_target: str = "proposal-writing",
    prior_outcome_str: str = "succeeded",
) -> Callable[[type[BaseModel], str], BaseModel]:
    """Factory for cycle-2 mock responses. Prior target is validated; new bet targets rank-2."""
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    # Cycle 2 targets rank-2 workflow (lead-qualification) since rank-1 was validated.
    rank2_id = next(w.workflow_id for w in leverage.per_workflow if w.rank == 2)
    bet = _bet_for(parsed, leverage)
    bet = bet.model_copy(update={"target_workflow_id": rank2_id})
    risk_map = _risk_and_agency_map_for(parsed)
    prior_run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    outcome = _outcome_report_for(prior_run_id)
    playbook = _continuation_playbook_for(
        workflow_map, leverage, bet, prior_target, prior_outcome_str
    )
    accepted = _accepted_eval_report()

    def factory(schema: type[BaseModel], prompt: str) -> BaseModel:
        if schema is ParsedIntake:
            return parsed
        if schema is WorkflowMap:
            return workflow_map
        if schema is LeverageAnalysis:
            return leverage
        if schema is ThirtyDayBet:
            return bet
        if schema is RiskAndAgencyMap:
            return risk_map
        if schema is FirstPlaybook:
            return playbook
        if schema is OutcomeReport:
            return outcome
        if schema is EvalReport:
            return accepted
        raise TypeError(f"No continuation factory branch for {schema.__name__}")

    return factory


# ---------- Pytest fixtures ----------


@pytest.fixture
def store() -> Iterator[SQLiteStore]:
    s = SQLiteStore(":memory:")
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def intake() -> AuditIntake:
    path = FIXTURES_DIR / "synthetic_consultant.json"
    return AuditIntake.model_validate(json.loads(path.read_text()))


@pytest.fixture
def ctx(store: SQLiteStore, intake: AuditIntake) -> AgentContext:
    provider = MockLLMProvider(structured_factory=_make_factory(intake))
    return AgentContext(tenant_id="default", provider=provider, store=store)


@pytest.fixture
def outcome_report() -> OutcomeReport:
    path = OUTCOMES_DIR / "synthetic_consultant_cycle1_outcome.json"
    return OutcomeReport.model_validate(json.loads(path.read_text()))


@pytest.fixture
def continuation_ctx(store: SQLiteStore, intake: AuditIntake) -> AgentContext:
    provider = MockLLMProvider(structured_factory=_make_continuation_factory(intake))
    return AgentContext(tenant_id="default", provider=provider, store=store)

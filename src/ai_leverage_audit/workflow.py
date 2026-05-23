"""AI Leverage Audit workflow orchestration (PRODUCT_MVP.md §4)."""

from __future__ import annotations

from uuid import UUID

from leverage_platform.runtime import AgentContext, run_workflow
from leverage_platform.schemas import EvalReport

from ai_leverage_audit.agents import (
    bet_designer_agent,
    continuation_critic_eval_agent,
    critic_eval_agent,
    intake_parser_agent,
    leverage_analyst_agent,
    playbook_builder_agent,
    risk_mapper_agent,
    workflow_diagnoser_agent,
)
from ai_leverage_audit.eval_config import AuditState, ContinuationAuditState
from ai_leverage_audit.schemas import (
    AuditIntake,
    FirstPlaybook,
    OutcomeReport,
    ParsedIntake,
    WorkflowMap,
)


async def run_audit(
    ctx: AgentContext, intake: AuditIntake
) -> tuple[UUID, EvalReport]:
    """Run the full AI Leverage Audit on one validated intake.

    Returns (workflow_run_id, EvalReport). Six intermediate artifacts plus
    the EvalReport persist via the platform's Artifact primitive.
    """

    async def body(ctx: AgentContext) -> EvalReport:
        parsed = await intake_parser_agent(ctx, intake)
        workflow_map = await workflow_diagnoser_agent(ctx, parsed)
        leverage = await leverage_analyst_agent(ctx, parsed, workflow_map)
        bet = await bet_designer_agent(ctx, parsed, leverage)
        risk_map = await risk_mapper_agent(ctx, parsed, workflow_map, leverage, bet)
        playbook = await playbook_builder_agent(
            ctx, parsed, workflow_map, leverage, bet, risk_map
        )
        state = AuditState(
            parsed_intake=parsed,
            workflow_map=workflow_map,
            leverage_analysis=leverage,
            thirty_day_bet=bet,
            risk_and_agency_map=risk_map,
            first_playbook=playbook,
        )
        return await critic_eval_agent(ctx, state)

    return await run_workflow(name="ai_leverage_audit", ctx=ctx, body=body)


async def run_reflection(
    ctx: AgentContext,
    outcome_report: OutcomeReport,
    prior_parsed_intake: ParsedIntake,
    prior_workflow_map: WorkflowMap,
    prior_playbook: FirstPlaybook,
    new_intake: AuditIntake | None = None,
) -> tuple[UUID, EvalReport]:
    """Run a continuation audit after a 30-day bet cycle completes.

    Reuses the prior cycle's parsed intake and workflow map unless new_intake
    is provided (owner reports their business has changed). Returns
    (workflow_run_id, EvalReport). 5-6 artifacts persist via the platform.
    """

    async def body(ctx: AgentContext) -> EvalReport:
        if new_intake is not None:
            parsed = await intake_parser_agent(ctx, new_intake)
            workflow_map = await workflow_diagnoser_agent(ctx, parsed)
        else:
            parsed = prior_parsed_intake
            workflow_map = prior_workflow_map

        leverage = await leverage_analyst_agent(
            ctx, parsed, workflow_map, prior_playbook=prior_playbook
        )
        bet = await bet_designer_agent(
            ctx, parsed, leverage, prior_outcome=outcome_report
        )
        risk_map = await risk_mapper_agent(ctx, parsed, workflow_map, leverage, bet)
        playbook = await playbook_builder_agent(
            ctx, parsed, workflow_map, leverage, bet, risk_map,
            prior_playbook=prior_playbook,
        )
        state = ContinuationAuditState(
            parsed_intake=parsed,
            workflow_map=workflow_map,
            leverage_analysis=leverage,
            thirty_day_bet=bet,
            risk_and_agency_map=risk_map,
            first_playbook=playbook,
            outcome_report=outcome_report,
            prior_playbook=prior_playbook,
        )
        return await continuation_critic_eval_agent(ctx, state)

    return await run_workflow(name="ai_leverage_reflection", ctx=ctx, body=body)

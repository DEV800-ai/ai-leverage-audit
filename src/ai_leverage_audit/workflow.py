"""AI Leverage Audit workflow orchestration (PRODUCT_MVP.md §4)."""

from __future__ import annotations

from uuid import UUID

from leverage_platform.runtime import AgentContext, run_workflow
from leverage_platform.schemas import EvalReport

from ai_leverage_audit.agents import (
    bet_designer_agent,
    critic_eval_agent,
    intake_parser_agent,
    leverage_analyst_agent,
    playbook_builder_agent,
    risk_mapper_agent,
    workflow_diagnoser_agent,
)
from ai_leverage_audit.eval_config import AuditState
from ai_leverage_audit.schemas import AuditIntake


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
        risk_map = await risk_mapper_agent(ctx, parsed, workflow_map, leverage)
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

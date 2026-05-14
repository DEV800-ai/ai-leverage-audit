"""The 7 agents of the AI Leverage Audit (PRODUCT_MVP.md §4).

    AuditIntake
      → intake_parser_agent        → ParsedIntake
      → workflow_diagnoser_agent   → WorkflowMap
      → leverage_analyst_agent     → LeverageAnalysis
      → bet_designer_agent         → ThirtyDayBet
      → risk_mapper_agent          → RiskAndAgencyMap
      → playbook_builder_agent     → FirstPlaybook
      → critic_eval_agent          → EvalReport (pure)

Per-Audit footprint: 1 WorkflowRun + 7 AgentRuns (8 with judge) + 7 Artifacts.
"""

from __future__ import annotations

import json

from leverage_platform.eval import llm_judge, rule_eval
from leverage_platform.llm import LLMParameters
from leverage_platform.runtime import AgentContext, agent
from leverage_platform.schemas import EvalReport
from pydantic import BaseModel

from ai_leverage_audit.eval_config import (
    LEVERAGE_AUDIT_RUBRIC,
    LEVERAGE_AUDIT_RULES,
    AuditState,
)
from ai_leverage_audit.prompts import (
    BET_DESIGNER_PROMPT,
    INTAKE_PARSER_PROMPT,
    LEVERAGE_ANALYST_PROMPT,
    PLAYBOOK_BUILDER_PROMPT,
    RISK_MAPPER_PROMPT,
    WORKFLOW_DIAGNOSER_PROMPT,
)
from ai_leverage_audit.schemas import (
    AuditIntake,
    FirstPlaybook,
    LeverageAnalysis,
    ParsedIntake,
    RiskAndAgencyMap,
    ThirtyDayBet,
    WorkflowMap,
)


def _j(model: BaseModel) -> str:
    """Stable JSON serialization for prompt variables and input hashing."""
    return json.dumps(model.model_dump(mode="json"), sort_keys=True)


# ---------- 1. Intake parser ----------


@agent(
    name="intake_parser_agent",
    schema=ParsedIntake,
    prompt_name="intake_parser_agent.v1",
    artifact_type="parsed_intake",
)
async def intake_parser_agent(ctx: AgentContext, intake: AuditIntake) -> ParsedIntake:
    result = await ctx.invoke_llm(
        template=INTAKE_PARSER_PROMPT,
        variables={"intake_json": _j(intake)},
        schema=ParsedIntake,
        prompt_name="intake_parser_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.0),
    )
    return result.value


# ---------- 2. Workflow diagnoser ----------


@agent(
    name="workflow_diagnoser_agent",
    schema=WorkflowMap,
    prompt_name="workflow_diagnoser_agent.v1",
    artifact_type="workflow_map",
)
async def workflow_diagnoser_agent(
    ctx: AgentContext, parsed: ParsedIntake
) -> WorkflowMap:
    result = await ctx.invoke_llm(
        template=WORKFLOW_DIAGNOSER_PROMPT,
        variables={"parsed_intake_json": _j(parsed)},
        schema=WorkflowMap,
        prompt_name="workflow_diagnoser_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.2),
    )
    return result.value


# ---------- 3. Leverage analyst ----------


@agent(
    name="leverage_analyst_agent",
    schema=LeverageAnalysis,
    prompt_name="leverage_analyst_agent.v1",
    artifact_type="leverage_analysis",
)
async def leverage_analyst_agent(
    ctx: AgentContext, parsed: ParsedIntake, workflow_map: WorkflowMap
) -> LeverageAnalysis:
    result = await ctx.invoke_llm(
        template=LEVERAGE_ANALYST_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "workflow_map_json": _j(workflow_map),
        },
        schema=LeverageAnalysis,
        prompt_name="leverage_analyst_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.3),
    )
    return result.value


# ---------- 4. Bet designer ----------


@agent(
    name="bet_designer_agent",
    schema=ThirtyDayBet,
    prompt_name="bet_designer_agent.v1",
    artifact_type="thirty_day_bet",
)
async def bet_designer_agent(
    ctx: AgentContext, parsed: ParsedIntake, leverage: LeverageAnalysis
) -> ThirtyDayBet:
    result = await ctx.invoke_llm(
        template=BET_DESIGNER_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "leverage_analysis_json": _j(leverage),
        },
        schema=ThirtyDayBet,
        prompt_name="bet_designer_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.2),
    )
    return result.value


# ---------- 5. Risk mapper ----------


@agent(
    name="risk_mapper_agent",
    schema=RiskAndAgencyMap,
    prompt_name="risk_mapper_agent.v1",
    artifact_type="risk_agency_map",
)
async def risk_mapper_agent(
    ctx: AgentContext,
    parsed: ParsedIntake,
    workflow_map: WorkflowMap,
    leverage: LeverageAnalysis,
) -> RiskAndAgencyMap:
    result = await ctx.invoke_llm(
        template=RISK_MAPPER_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "workflow_map_json": _j(workflow_map),
            "leverage_analysis_json": _j(leverage),
        },
        schema=RiskAndAgencyMap,
        prompt_name="risk_mapper_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.2),
    )
    return result.value


# ---------- 6. Playbook builder ----------


@agent(
    name="playbook_builder_agent",
    schema=FirstPlaybook,
    prompt_name="playbook_builder_agent.v1",
    artifact_type="first_playbook",
)
async def playbook_builder_agent(
    ctx: AgentContext,
    parsed: ParsedIntake,
    workflow_map: WorkflowMap,
    leverage: LeverageAnalysis,
    bet: ThirtyDayBet,
    risk_map: RiskAndAgencyMap,
) -> FirstPlaybook:
    result = await ctx.invoke_llm(
        template=PLAYBOOK_BUILDER_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "workflow_map_json": _j(workflow_map),
            "leverage_analysis_json": _j(leverage),
            "thirty_day_bet_json": _j(bet),
            "risk_and_agency_map_json": _j(risk_map),
        },
        schema=FirstPlaybook,
        prompt_name="playbook_builder_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.2),
    )
    return result.value


# ---------- 7. Critic eval (pure) ----------


@agent(
    name="critic_eval_agent",
    schema=EvalReport,
    prompt_name="critic_eval_agent.v1",
    pure=True,
    artifact_type="eval_report",
)
async def critic_eval_agent(ctx: AgentContext, state: AuditState) -> EvalReport:
    """Two-stage eval: deterministic rules first, LLM judge only if rules pass."""
    rule_report = rule_eval(state, LEVERAGE_AUDIT_RULES)
    if not rule_report.accepted:
        return rule_report
    return await llm_judge(ctx, artifact=state, rubric=LEVERAGE_AUDIT_RUBRIC)

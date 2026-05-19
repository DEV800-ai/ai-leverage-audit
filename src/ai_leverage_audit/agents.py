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
    CONTINUATION_AUDIT_RULES,
    LEVERAGE_AUDIT_RUBRIC,
    LEVERAGE_AUDIT_RULES,
    AuditState,
    ContinuationAuditState,
)
from ai_leverage_audit.prompts import (
    BET_DESIGNER_PROMPT,
    INTAKE_PARSER_PROMPT,
    LEVERAGE_ANALYST_PROMPT,
    OUTCOME_PARSER_PROMPT,
    PLAYBOOK_BUILDER_PROMPT,
    RISK_MAPPER_PROMPT,
    WORKFLOW_DIAGNOSER_PROMPT,
)
from ai_leverage_audit.schemas import (
    AuditIntake,
    FirstPlaybook,
    LeverageAnalysis,
    OutcomeReport,
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
    ctx: AgentContext,
    parsed: ParsedIntake,
    workflow_map: WorkflowMap,
    prior_playbook: FirstPlaybook | None = None,
) -> LeverageAnalysis:
    prior_section = ""
    if prior_playbook is not None:
        rejected = [e.workflow_id for e in prior_playbook.workflow_entries if e.current_status == "rejected"]
        validated = [e.workflow_id for e in prior_playbook.workflow_entries if e.current_status == "validated"]
        parts = [f"PRIOR CYCLE CONTEXT (cycle {prior_playbook.cycle_number}):"]
        if rejected:
            parts.append(f"  Never rank these (rejected in a prior cycle): {rejected}")
        if validated:
            parts.append(f"  Down-rank these (already validated, deepening later is fine): {validated}")
        parts.append("  Cite how prior outcomes inform this ranking.")
        prior_section = "\n".join(parts)
    result = await ctx.invoke_llm(
        template=LEVERAGE_ANALYST_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "workflow_map_json": _j(workflow_map),
            "prior_playbook_section": prior_section,
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
    ctx: AgentContext,
    parsed: ParsedIntake,
    leverage: LeverageAnalysis,
    prior_outcome: OutcomeReport | None = None,
) -> ThirtyDayBet:
    prior_section = ""
    if prior_outcome is not None:
        prior_section = (
            f"CYCLE CONTINUITY RULE (mandatory):\n"
            f"  Prior bet: {prior_outcome.prior_bet_title!r}\n"
            f"  Outcome: {prior_outcome.outcome} (intent: {prior_outcome.intent})\n"
            f"  What worked: {prior_outcome.what_worked_text}\n"
            f"  What to change: {prior_outcome.what_owner_would_change_text}\n"
            f"  The hypothesis MUST reference this prior outcome: "
            f"'Last cycle we found X; this cycle we test Y because...'\n"
            f"  Never target a workflow with status 'rejected' in the prior playbook."
        )
    result = await ctx.invoke_llm(
        template=BET_DESIGNER_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "leverage_analysis_json": _j(leverage),
            "prior_outcome_section": prior_section,
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
    prior_playbook: FirstPlaybook | None = None,
) -> FirstPlaybook:
    prior_section = ""
    if prior_playbook is not None:
        next_cycle = prior_playbook.cycle_number + 1
        prior_section = (
            f"CONTINUATION PLAYBOOK RULES (mandatory):\n"
            f"  This is cycle {next_cycle}. Set cycle_number = {next_cycle}.\n"
            f"  UPDATE the prior playbook — do NOT create a new one from scratch.\n"
            f"  Prior playbook (JSON): {_j(prior_playbook)}\n"
            f"  Status evolution rules:\n"
            f"    - The workflow targeted by this cycle's bet → set current_status\n"
            f"      based on the outcome stored in prior_outcome_section.\n"
            f"    - Workflows not touched this cycle → preserve prior status.\n"
            f"    - New workflows (appear in workflow_map but not prior) → 'not_yet_tested'.\n"
            f"  Fill cycle_introduced: use prior value if it exists, else {next_cycle}.\n"
            f"  Fill last_outcome_summary ONLY for the workflow targeted this cycle\n"
            f"  (1 short sentence summarising what happened to it)."
        )
    result = await ctx.invoke_llm(
        template=PLAYBOOK_BUILDER_PROMPT,
        variables={
            "parsed_intake_json": _j(parsed),
            "workflow_map_json": _j(workflow_map),
            "leverage_analysis_json": _j(leverage),
            "thirty_day_bet_json": _j(bet),
            "risk_and_agency_map_json": _j(risk_map),
            "prior_playbook_section": prior_section,
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


# ---------- 8. Outcome parser (cycle 2+) ----------


@agent(
    name="outcome_parser_agent",
    schema=OutcomeReport,
    prompt_name="outcome_parser_agent.v1",
    artifact_type="outcome_report",
)
async def outcome_parser_agent(
    ctx: AgentContext, prior_bet: ThirtyDayBet, outcome_text: str
) -> OutcomeReport:
    """Parse free-text owner reflection into a structured OutcomeReport."""
    result = await ctx.invoke_llm(
        template=OUTCOME_PARSER_PROMPT,
        variables={
            "prior_bet_json": _j(prior_bet),
            "outcome_text": outcome_text,
        },
        schema=OutcomeReport,
        prompt_name="outcome_parser_agent",
        prompt_version="v1",
        parameters=LLMParameters(temperature=0.0),
    )
    return result.value


# ---------- 9. Continuation critic eval (cycle 2+, pure) ----------


@agent(
    name="continuation_critic_eval_agent",
    schema=EvalReport,
    prompt_name="continuation_critic_eval_agent.v1",
    pure=True,
    artifact_type="eval_report",
)
async def continuation_critic_eval_agent(
    ctx: AgentContext, state: ContinuationAuditState
) -> EvalReport:
    """Two-stage eval for continuation audits: runs base rules + continuation rules."""
    base_state = AuditState(
        parsed_intake=state.parsed_intake,
        workflow_map=state.workflow_map,
        leverage_analysis=state.leverage_analysis,
        thirty_day_bet=state.thirty_day_bet,
        risk_and_agency_map=state.risk_and_agency_map,
        first_playbook=state.first_playbook,
    )
    rule_report = rule_eval(base_state, LEVERAGE_AUDIT_RULES)
    if not rule_report.accepted:
        return rule_report
    cont_report = rule_eval(state, CONTINUATION_AUDIT_RULES)
    if not cont_report.accepted:
        return cont_report
    return await llm_judge(ctx, artifact=base_state, rubric=LEVERAGE_AUDIT_RUBRIC)

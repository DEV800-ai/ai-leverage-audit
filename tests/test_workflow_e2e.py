"""Gate 2 acceptance test for the AI Leverage Audit workflow.

Per PRODUCT_MVP.md Gate 2 / §7:
- The full Audit runs end-to-end on the synthetic intake.
- Per run: 1 WorkflowRun + 7 AgentRuns (8 with judge) + 7 Artifacts,
  all status="succeeded".
- EvalReport.accepted is True (factory produces rule-passing artifacts;
  mock judge approves).
- All 7 AgentRun rows have prompt_version="v1" (audit correctness).
- Cost attributed to tenant_id="default".

Uses MockLLMProvider — no Anthropic tokens spent.

An additional opt-in live test runs the same workflow against real
Anthropic when RUN_LIVE_TESTS=1 is set in the environment.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from leverage_platform.runtime import AgentContext
from leverage_platform.schemas import EvalReport
from leverage_platform.storage import SQLiteStore

from ai_leverage_audit.schemas import AuditIntake
from ai_leverage_audit.workflow import run_audit


async def test_audit_runs_end_to_end_against_mock_provider(
    ctx: AgentContext, store: SQLiteStore, intake: AuditIntake
) -> None:
    workflow_id, report = await run_audit(ctx, intake)

    # 1. Typed EvalReport accepted.
    assert isinstance(report, EvalReport)
    assert report.accepted is True, f"unexpected rejection: {report.summary}"

    # 2. Exactly one WorkflowRun, succeeded.
    wf_rows = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT id, status, started_at, ended_at, workflow_name FROM workflow_run"
    ).fetchall()
    assert len(wf_rows) == 1
    assert str(workflow_id) == wf_rows[0]["id"]
    assert wf_rows[0]["status"] == "succeeded"
    assert wf_rows[0]["workflow_name"] == "ai_leverage_audit"
    assert wf_rows[0]["ended_at"] is not None

    # 3. AgentRun sequence: 6 LLM agents + critic + judge = 8.
    agent_rows = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT agent_name, status, model, prompt_version FROM agent_run "
        "WHERE workflow_run_id = ? ORDER BY started_at",
        (str(workflow_id),),
    ).fetchall()
    names = [r["agent_name"] for r in agent_rows]
    assert names == [
        "intake_parser_agent",
        "workflow_diagnoser_agent",
        "leverage_analyst_agent",
        "bet_designer_agent",
        "risk_mapper_agent",
        "playbook_builder_agent",
        "critic_eval_agent",
        "llm_judge",
    ], f"unexpected agent sequence: {names}"

    # All AgentRuns succeeded.
    assert all(r["status"] == "succeeded" for r in agent_rows)

    # 4. prompt_version persisted on every non-pure agent (audit correctness).
    critic_row = next(r for r in agent_rows if r["agent_name"] == "critic_eval_agent")
    assert critic_row["model"] == "(none)", "critic is pure — model is sentinel"
    non_pure = [r for r in agent_rows if r["agent_name"] != "critic_eval_agent"]
    for r in non_pure:
        # llm_judge is platform-side; the product's 6 LLM agents all set v1.
        if r["agent_name"] != "llm_judge":
            assert r["prompt_version"] == "v1", (
                f"agent {r['agent_name']} missing prompt_version=v1; "
                f"got {r['prompt_version']!r}"
            )

    # 5. Artifact rows: 7 (one per outer agent + critic eval report).
    artifact_rows = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT type, schema_name FROM artifact WHERE workflow_run_id = ? "
        "ORDER BY created_at",
        (str(workflow_id),),
    ).fetchall()
    types = [r["type"] for r in artifact_rows]
    assert types == [
        "parsed_intake",
        "workflow_map",
        "leverage_analysis",
        "thirty_day_bet",
        "risk_agency_map",
        "first_playbook",
        "eval_report",
    ], f"unexpected artifact sequence: {types}"

    # Schemas are versioned per ADR-004.
    for r in artifact_rows:
        assert "@v1" in r["schema_name"], r["schema_name"]

    # 6. Cost attributed to tenant_id="default".
    cost_entries = await store.query_cost(
        "default", since=datetime(2020, 1, 1, tzinfo=UTC)
    )
    assert len(cost_entries) == 1
    assert cost_entries[0].tenant_id == "default"
    assert cost_entries[0].cost_usd > Decimal("0")
    assert cost_entries[0].call_count == 8


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1",
    reason="Live LLM test gated by RUN_LIVE_TESTS=1",
)
async def test_audit_runs_end_to_end_against_real_llm(
    store: SQLiteStore, intake: AuditIntake
) -> None:
    """Opt-in test: run the Audit against a real LLM provider.

    Provider selection by env var (same as the CLI):
    - LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY (default)
    - LLM_PROVIDER=openai + OPENAI_API_KEY
    Costs real money. Set RUN_LIVE_TESTS=1 to enable.
    """
    choice = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if choice == "anthropic":
        from leverage_platform.llm import AnthropicProvider

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set; cannot run live test")
        provider: object = AnthropicProvider(api_key=api_key)
    elif choice == "openai":
        from leverage_platform.llm import OpenAIProvider

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set; cannot run live test")
        provider = OpenAIProvider(api_key=api_key)
    else:
        pytest.fail(f"unknown LLM_PROVIDER={choice!r}")

    ctx = AgentContext(tenant_id="default", provider=provider, store=store)

    workflow_id, report = await run_audit(ctx, intake)
    assert isinstance(report, EvalReport)
    # Live behaviour: report may be rejected by a strict judge — but the
    # workflow must complete without raising and the WorkflowRun must
    # succeed structurally.
    wf_rows = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT status FROM workflow_run WHERE id = ?",
        (str(workflow_id),),
    ).fetchall()
    assert wf_rows[0]["status"] == "succeeded"

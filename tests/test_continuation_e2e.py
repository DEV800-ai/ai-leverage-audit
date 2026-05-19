"""End-to-end tests for run_reflection (Stage 3 — Evolve).

Uses the mock provider so no LLM tokens are spent. Mirrors the structure
of test_workflow_e2e.py for the continuation audit path.
"""

from __future__ import annotations

import pytest
from leverage_platform.runtime import AgentContext
from leverage_platform.storage import SQLiteStore

from ai_leverage_audit.schemas import AuditIntake, OutcomeReport
from ai_leverage_audit.workflow import run_reflection
from tests.conftest import (
    _leverage_analysis_for,
    _outcome_report_for,
    _parsed_intake_for,
    _playbook_for,
    _workflow_map_for,
    _bet_for,
)
from uuid import UUID


def _prior_artifacts(intake: AuditIntake):
    """Build the prior-cycle artifacts needed as run_reflection inputs."""
    parsed = _parsed_intake_for(intake)
    workflow_map = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(workflow_map)
    bet = _bet_for(parsed, leverage)
    playbook = _playbook_for(workflow_map, leverage, bet)
    return parsed, workflow_map, playbook


async def test_run_reflection_succeeds(
    continuation_ctx: AgentContext,
    store: SQLiteStore,
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """run_reflection returns accepted EvalReport with the mock provider."""
    parsed, workflow_map, prior_playbook = _prior_artifacts(intake)

    workflow_id, report = await run_reflection(
        continuation_ctx,
        outcome_report,
        parsed,
        workflow_map,
        prior_playbook,
    )

    assert report.accepted is True, f"reflection rejected: {report.summary}"
    assert workflow_id is not None


async def test_run_reflection_persists_artifacts(
    continuation_ctx: AgentContext,
    store: SQLiteStore,
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """Continuation audit persists 5-6 artifacts (no intake_parser or workflow_diagnoser)."""
    import sqlite3

    parsed, workflow_map, prior_playbook = _prior_artifacts(intake)

    workflow_id, _ = await run_reflection(
        continuation_ctx,
        outcome_report,
        parsed,
        workflow_map,
        prior_playbook,
    )

    rows = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT type FROM artifact WHERE workflow_run_id = ?",
        (str(workflow_id),),
    ).fetchall()
    artifact_types = {r[0] for r in rows}

    # These 5 artifact types are always produced in run_reflection.
    for expected in (
        "leverage_analysis", "thirty_day_bet", "risk_agency_map",
        "first_playbook", "eval_report",
    ):
        assert expected in artifact_types, f"missing artifact: {expected}"

    # Intake parser and workflow diagnoser are skipped (reuse path).
    assert "parsed_intake" not in artifact_types
    assert "workflow_map" not in artifact_types


async def test_run_reflection_cycle_number_incremented(
    continuation_ctx: AgentContext,
    store: SQLiteStore,
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """The returned playbook has cycle_number > 1."""
    import json
    import sqlite3

    parsed, workflow_map, prior_playbook = _prior_artifacts(intake)

    workflow_id, report = await run_reflection(
        continuation_ctx,
        outcome_report,
        parsed,
        workflow_map,
        prior_playbook,
    )

    assert report.accepted

    row = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT data FROM artifact WHERE workflow_run_id = ? AND type = 'first_playbook'",
        (str(workflow_id),),
    ).fetchone()
    assert row is not None
    playbook_data = json.loads(row[0])
    assert playbook_data["cycle_number"] == 2


async def test_run_reflection_prior_target_status_evolved(
    continuation_ctx: AgentContext,
    store: SQLiteStore,
    intake: AuditIntake,
    outcome_report: OutcomeReport,
) -> None:
    """The prior cycle's target workflow appears as 'validated' after a succeeded outcome."""
    import json

    parsed, workflow_map, prior_playbook = _prior_artifacts(intake)
    prior_target = prior_playbook.workflow_entries[
        next(
            i for i, e in enumerate(prior_playbook.workflow_entries)
            if e.current_status == "experimenting"
        )
    ].workflow_id

    workflow_id, report = await run_reflection(
        continuation_ctx,
        outcome_report,
        parsed,
        workflow_map,
        prior_playbook,
    )

    assert report.accepted

    row = store._conn.execute(  # type: ignore[attr-defined]
        "SELECT data FROM artifact WHERE workflow_run_id = ? AND type = 'first_playbook'",
        (str(workflow_id),),
    ).fetchone()
    playbook_data = json.loads(row[0])
    entry = next(e for e in playbook_data["workflow_entries"] if e["workflow_id"] == prior_target)
    assert entry["current_status"] == "validated"

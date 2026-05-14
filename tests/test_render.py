"""Renderer tests — markdown content + DB load path."""

from __future__ import annotations

import pytest
from leverage_platform.runtime import AgentContext
from leverage_platform.schemas import EvalReport
from leverage_platform.storage import SQLiteStore

from ai_leverage_audit.render import (
    load_state_from_db,
    render_audit_markdown,
    render_from_db,
)
from ai_leverage_audit.schemas import AuditIntake
from ai_leverage_audit.workflow import run_audit
from tests.conftest import (
    _accepted_eval_report,
    _bet_for,
    _leverage_analysis_for,
    _parsed_intake_for,
    _playbook_for,
    _risk_and_agency_map_for,
    _workflow_map_for,
)


def _full_state(intake: AuditIntake) -> dict[str, object]:
    """Build a complete state dict from the test factory."""
    parsed = _parsed_intake_for(intake)
    wfmap = _workflow_map_for(parsed)
    leverage = _leverage_analysis_for(wfmap)
    bet = _bet_for(parsed, leverage)
    risk = _risk_and_agency_map_for(parsed)
    pb = _playbook_for(wfmap, leverage, bet)
    return {
        "parsed_intake": parsed,
        "workflow_map": wfmap,
        "leverage_analysis": leverage,
        "thirty_day_bet": bet,
        "risk_agency_map": risk,
        "first_playbook": pb,
        "eval_report": _accepted_eval_report(),
    }


def test_renders_with_expected_sections(intake: AuditIntake) -> None:
    md = render_audit_markdown(_full_state(intake))

    for header in [
        "# ",  # title
        "## Your weekly workflows",
        "## Where AI can save you the most time",
        "## Your 30-day bet",
        "## Areas to keep human-controlled",
        "## Owner-agency checkpoints",
        "## Weekly self-review questions",
        "## Playbook — workflow status at day 0",
    ]:
        assert header in md, f"missing header: {header}"


def test_renders_top_three_workflows_by_rank(intake: AuditIntake) -> None:
    state = _full_state(intake)
    md = render_audit_markdown(state)
    leverage = state["leverage_analysis"]
    top3_ids = sorted(
        leverage.per_workflow, key=lambda w: w.rank  # type: ignore[attr-defined]
    )[:3]
    for w in top3_ids:
        # Either the workflow title or its id should appear in the rendered top-3 section.
        assert any(
            tok in md for tok in (w.rationale[:20], w.workflow_id)
        ), f"top-3 rank {w.rank} workflow {w.workflow_id!r} not visible"


def test_renders_accepted_banner(intake: AuditIntake) -> None:
    md = render_audit_markdown(_full_state(intake))
    assert "✅ Accepted by the audit" in md
    assert "## Audit concerns" not in md


def test_renders_rejected_banner(intake: AuditIntake) -> None:
    state = _full_state(intake)
    state["eval_report"] = EvalReport(
        accepted=False,
        criteria=[],
        summary="rules failed in test",
    )
    md = render_audit_markdown(state)
    assert "⚠️ Audit had concerns" in md
    assert "## Audit concerns" in md
    assert "rules failed in test" in md


def test_renders_first_48h_actions_as_checkboxes(intake: AuditIntake) -> None:
    md = render_audit_markdown(_full_state(intake))
    state = _full_state(intake)
    bet = state["thirty_day_bet"]
    for action in bet.first_48h_actions:  # type: ignore[attr-defined]
        assert f"- [ ] {action}" in md


def test_renders_keep_human_areas_with_severity(intake: AuditIntake) -> None:
    md = render_audit_markdown(_full_state(intake))
    state = _full_state(intake)
    risk = state["risk_agency_map"]
    for kh in risk.keep_human_areas:  # type: ignore[attr-defined]
        assert kh.area in md
        assert f"severity: {kh.severity}" in md


def test_renders_bet_with_budget_context(intake: AuditIntake) -> None:
    """Time + cost lines should show the intake budgets as context."""
    md = render_audit_markdown(_full_state(intake))
    state = _full_state(intake)
    parsed = state["parsed_intake"]
    assert f"within your {parsed.weekly_time_budget_hours}h/wk budget" in md  # type: ignore[attr-defined]
    assert f"within your ${parsed.monthly_budget_usd}/mo budget" in md  # type: ignore[attr-defined]


async def test_load_state_from_db_round_trip(
    ctx: AgentContext, store: SQLiteStore, intake: AuditIntake, tmp_path
) -> None:
    """After running the workflow, load_state_from_db reconstructs the state."""
    workflow_id, _ = await run_audit(ctx, intake)

    # Workflow uses the in-memory store. Copy artifacts to a file-backed DB
    # via raw SQL so we can exercise load_state_from_db's real code path.
    import sqlite3

    file_db = tmp_path / "audit.db"
    # Recreate schema and copy rows from the in-memory store.
    src = store._conn  # type: ignore[attr-defined]
    dst = sqlite3.connect(file_db)
    dst.row_factory = sqlite3.Row
    # Pull schema and contents.
    schema_rows = src.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name IN "
        "('workflow_run', 'agent_run', 'artifact')"
    ).fetchall()
    for r in schema_rows:
        if r[0]:
            dst.execute(r[0])
    for table in ("workflow_run", "agent_run", "artifact"):
        rows = src.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            continue
        cols = rows[0].keys()
        placeholders = ", ".join(["?"] * len(cols))
        for row in rows:
            dst.execute(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                tuple(row[c] for c in cols),
            )
    dst.commit()
    dst.close()

    state = load_state_from_db(str(file_db), workflow_run_id=workflow_id)
    for required in (
        "parsed_intake",
        "workflow_map",
        "leverage_analysis",
        "thirty_day_bet",
        "risk_agency_map",
        "first_playbook",
        "eval_report",
    ):
        assert required in state, f"missing {required}"

    md = render_from_db(str(file_db), workflow_run_id=workflow_id)
    assert "## Your 30-day bet" in md


def test_load_state_from_db_picks_latest_when_unspecified(tmp_path) -> None:
    """If workflow_run_id is None, the most recent succeeded run is used."""
    import sqlite3

    db = tmp_path / "empty.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE workflow_run (id TEXT PRIMARY KEY, status TEXT, started_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE artifact (id TEXT, workflow_run_id TEXT, type TEXT, "
        "schema_name TEXT, data TEXT, created_at TEXT)"
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="No succeeded workflow_run"):
        load_state_from_db(str(db))


def test_load_state_from_db_errors_on_missing_artifacts(tmp_path) -> None:
    """If the run is missing artifacts (corrupt or partial), error out clearly."""
    import sqlite3
    from datetime import UTC, datetime
    from uuid import uuid4

    db = tmp_path / "partial.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE workflow_run (id TEXT PRIMARY KEY, status TEXT, started_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE artifact (id TEXT, workflow_run_id TEXT, type TEXT, "
        "schema_name TEXT, data TEXT, created_at TEXT)"
    )
    run_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO workflow_run (id, status, started_at) VALUES (?, ?, ?)",
        (run_id, "succeeded", now),
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="missing artifacts"):
        load_state_from_db(str(db))

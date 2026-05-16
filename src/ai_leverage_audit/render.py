"""Markdown rendering for a complete Audit.

Turns the 6 LLM-produced artifacts + the EvalReport into a single
friend-shareable document. No LLM calls; pure rendering. Pull the
artifacts from the audit's SQLite store (see `load_state_from_db`),
or pass them directly.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import UUID

from leverage_platform.schemas import EvalReport

from ai_leverage_audit.schemas import (
    FirstPlaybook,
    LeverageAnalysis,
    ParsedIntake,
    RiskAndAgencyMap,
    ThirtyDayBet,
    WorkflowMap,
)

_TYPE_TO_SCHEMA: dict[str, type] = {
    "parsed_intake": ParsedIntake,
    "workflow_map": WorkflowMap,
    "leverage_analysis": LeverageAnalysis,
    "thirty_day_bet": ThirtyDayBet,
    "risk_agency_map": RiskAndAgencyMap,
    "first_playbook": FirstPlaybook,
    "eval_report": EvalReport,
}


def load_state_from_db(
    db_path: str, workflow_run_id: UUID | None = None
) -> dict[str, object]:
    """Load the 6 LLM artifacts + the EvalReport for a specific Audit run.

    If workflow_run_id is None, picks the most recent successful run.
    Returns a dict keyed by artifact type.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if workflow_run_id is None:
            row = conn.execute(
                "SELECT id FROM workflow_run WHERE status = 'succeeded' "
                "ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise ValueError(f"No succeeded workflow_run found in {db_path}")
            workflow_run_id = UUID(row["id"])

        rows = conn.execute(
            "SELECT type, data FROM artifact WHERE workflow_run_id = ? "
            "ORDER BY created_at",
            (str(workflow_run_id),),
        ).fetchall()
    finally:
        conn.close()

    state: dict[str, object] = {"workflow_run_id": workflow_run_id}
    for row in rows:
        t = row["type"]
        if t not in _TYPE_TO_SCHEMA:
            continue
        state[t] = _TYPE_TO_SCHEMA[t].model_validate(json.loads(row["data"]))

    required = set(_TYPE_TO_SCHEMA.keys())
    missing = required - {k for k in state if k != "workflow_run_id"}
    if missing:
        raise ValueError(
            f"Audit run {workflow_run_id} is missing artifacts: {sorted(missing)}"
        )

    return state


def render_audit_markdown(state: dict[str, object]) -> str:
    """Return a single markdown document covering the whole Audit."""
    parsed: ParsedIntake = state["parsed_intake"]  # type: ignore[assignment]
    workflow_map: WorkflowMap = state["workflow_map"]  # type: ignore[assignment]
    leverage: LeverageAnalysis = state["leverage_analysis"]  # type: ignore[assignment]
    bet: ThirtyDayBet = state["thirty_day_bet"]  # type: ignore[assignment]
    risk: RiskAndAgencyMap = state["risk_agency_map"]  # type: ignore[assignment]
    playbook: FirstPlaybook = state["first_playbook"]  # type: ignore[assignment]
    eval_report: EvalReport = state["eval_report"]  # type: ignore[assignment]

    out: list[str] = []

    # Header
    out.append(f"# {playbook.title}")
    out.append("")
    out.append(playbook.business_summary)
    out.append("")
    out.append(f"**Primary goal:** {parsed.primary_goal}")
    out.append("")

    # Status banner
    status_label = (
        "✅ Accepted by the audit"
        if eval_report.accepted
        else "⚠️ Audit had concerns — see end of doc"
    )
    out.append(f"_{status_label}_")
    out.append("")

    # Workflow map
    out.append("## Your weekly workflows")
    out.append("")
    out.append("| Workflow | Frequency | Volume | Time |")
    out.append("| --- | --- | --- | --- |")
    for wf in workflow_map.workflows:
        time_per_wk = wf.minutes_per_occurrence * wf.occurrences_per_week
        out.append(
            f"| **{wf.title}** ({wf.id}) "
            f"| {wf.frequency} "
            f"| {_fmt_num(wf.occurrences_per_week)}/wk × {_fmt_num(wf.minutes_per_occurrence)}min "
            f"| ~{_fmt_num(time_per_wk)}min/wk |"
        )
    out.append("")

    # Leverage analysis — top 3
    out.append("## Where AI can save you the most time")
    out.append("")
    sorted_levs = sorted(leverage.per_workflow, key=lambda w: w.rank)
    for w in sorted_levs[:3]:
        wf = _find_workflow(workflow_map, w.workflow_id)
        title = wf.title if wf else w.workflow_id
        conf_label = f" · _confidence: {w.confidence}_" if w.confidence else ""
        out.append(f"### #{w.rank} — {title}{conf_label}")
        out.append(f"_{w.rationale}_")
        out.append("")
        out.append(
            f"- Estimated time saved: **~{w.time_saved_hours_per_week_estimate}h/wk**"
        )
        out.append(
            f"- Risk if AI gets it wrong: {w.risk_if_ai_gets_it_wrong} · "
            f"Setup complexity: {w.setup_complexity} · "
            f"Human judgment needed: {w.human_judgment_needed}"
        )
        out.append(
            f"- Suggested mix: **{w.automate_pct}% automate** / "
            f"{w.assist_pct}% assist / **{w.keep_human_pct}% keep human**"
        )
        if w.evidence_from_intake:
            out.append("- Evidence from your intake:")
            for ev in w.evidence_from_intake:
                out.append(f"  - _{ev}_")
        if w.assumptions:
            out.append("- Assumptions (intake didn't say):")
            for a in w.assumptions:
                out.append(f"  - {a}")
        if w.automate_examples:
            out.append(f"  - Automate: {', '.join(w.automate_examples)}")
        if w.assist_examples:
            out.append(f"  - Assist: {', '.join(w.assist_examples)}")
        if w.keep_human_examples:
            out.append(f"  - Keep human: {', '.join(w.keep_human_examples)}")
        out.append("")

    # The bet
    out.append("## Your 30-day bet")
    out.append("")
    out.append(f"### {bet.title}")
    out.append("")
    out.append(f"> {bet.hypothesis}")
    out.append("")
    out.append("| | |")
    out.append("| --- | --- |")
    out.append(f"| **Target workflow** | `{bet.target_workflow_id}` |")
    out.append(f"| **Success metric** | {bet.success_metric} |")
    out.append(f"| **Failure metric** | {bet.failure_metric} |")
    out.append(
        f"| **Time investment** | {bet.estimated_weekly_time_hours}h/wk "
        f"(within your {parsed.weekly_time_budget_hours}h/wk budget) |"
    )
    out.append(
        f"| **Setup cost** | ${bet.estimated_setup_cost_usd} "
        f"(within your ${parsed.monthly_budget_usd}/mo budget) |"
    )
    out.append(f"| **Expected asset by day 30** | {bet.expected_asset_created} |")
    out.append("")

    out.append("#### Weekly plan")
    out.append("")
    for i, week in enumerate(bet.weekly_plan, 1):
        out.append(f"{i}. **Week {i}** — {_strip_week_prefix(week, i)}")
    out.append("")

    out.append("#### First 48 hours — start here")
    out.append("")
    for a in bet.first_48h_actions:
        out.append(f"- [ ] {a}")
    out.append("")

    # Keep human
    out.append("## Areas to keep human-controlled")
    out.append("")
    for kh in risk.keep_human_areas:
        out.append(f"- **{kh.area}** _(severity: {kh.severity})_ — {kh.reason}")
    out.append("")

    # Owner agency
    out.append("## Owner-agency checkpoints")
    out.append("")
    for cp in risk.agency_checkpoints:
        cadence = f" _({cp.cadence})_" if cp.cadence else ""
        out.append(f"- **When:** {cp.trigger}{cadence}")
        out.append(f"  **Do:** {cp.required_action}")
    out.append("")

    # Weekly review questions
    out.append("## Weekly self-review questions")
    out.append("")
    for q in risk.weekly_review_questions:
        out.append(f"- {q}")
    out.append("")

    # Playbook entries (compact)
    out.append("## Playbook — workflow status at day 0")
    out.append("")
    out.append("| Workflow | Status | Notes |")
    out.append("| --- | --- | --- |")
    for entry in playbook.workflow_entries:
        wf = _find_workflow(workflow_map, entry.workflow_id)
        title = wf.title if wf else entry.workflow_id
        out.append(f"| {title} | `{entry.current_status}` | {entry.summary} |")
    out.append("")

    if playbook.open_questions:
        out.append("### Open questions")
        out.append("")
        for q in playbook.open_questions:
            out.append(f"- {q}")
        out.append("")

    if playbook.rules_for_human_involvement:
        out.append("### Rules for human involvement")
        out.append("")
        for r in playbook.rules_for_human_involvement:
            out.append(f"- {r}")
        out.append("")

    # Eval footer
    out.append("---")
    out.append("")
    if eval_report.accepted:
        out.append(f"_{eval_report.summary}_")
    else:
        out.append("## Audit concerns")
        out.append("")
        out.append(f"_{eval_report.summary}_")
        out.append("")
        for c in eval_report.criteria:
            if not c.passed:
                out.append(f"- ❌ **{c.name}** — {c.reason}")

    out.append("")
    return "\n".join(out)


def _find_workflow(workflow_map: WorkflowMap, workflow_id: str):
    for w in workflow_map.workflows:
        if w.id == workflow_id:
            return w
    return None


def _strip_week_prefix(text: str, week_num: int) -> str:
    """If the LLM put 'Week N: ...' inside the plan entry, strip the prefix."""
    prefix = f"Week {week_num}:"
    if text.startswith(prefix):
        return text[len(prefix):].strip()
    return text


def _fmt_num(n: float) -> str:
    """Format a float without trailing .0 when it's whole."""
    if n == int(n):
        return str(int(n))
    return f"{n:.2f}".rstrip("0").rstrip(".")


def render_from_db(db_path: str, workflow_run_id: UUID | None = None) -> str:
    """Convenience: load + render in one call."""
    state = load_state_from_db(db_path, workflow_run_id=workflow_run_id)
    return render_audit_markdown(state)


def write_rendered(content: str, output_path: str) -> None:
    """Write rendered markdown to a path, or print to stdout if path is '-'."""
    if output_path == "-":
        print(content)
    else:
        Path(output_path).write_text(content)

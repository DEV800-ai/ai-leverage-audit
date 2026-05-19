"""Command-line entry point for the AI Leverage Audit.

`audit run --intake X.json --output X.json --markdown X.md` runs the full
workflow and produces both the JSON report and a friend-shareable
markdown render in one call. The markdown is skipped when the audit's
EvalReport is rejected — inspect the JSON in that case.

`audit render --db audit.db --output X.md` re-renders a completed run
from the SQLite store. Useful for older runs after iteration.

Environment variables consumed at runtime:
- LLM_PROVIDER: "anthropic" (default) or "openai".
- ANTHROPIC_API_KEY: required when LLM_PROVIDER=anthropic.
- OPENAI_API_KEY: required when LLM_PROVIDER=openai.
- LLM_MODEL: optional override for the provider's default model.
- AUDIT_DB: SQLite path (default: ./audit.db).
- AUDIT_TENANT_ID: tenant attribution (default: "default").
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from ai_leverage_audit import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit",
        description=(
            "AI Leverage Audit — diagnoses business workflows, scores AI "
            "leverage, designs a 30-day experiment. See PRODUCT_VISION.md and "
            "PRODUCT_MVP.md in the leverage-platform repo for the full spec."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"audit {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    run = subparsers.add_parser("run", help="Run the Audit on an intake JSON file.")
    run.add_argument("--intake", required=True, help="Path to intake JSON file.")
    run.add_argument(
        "--output",
        default="-",
        help="Path to write the Audit report JSON. Use '-' for stdout (default).",
    )
    run.add_argument(
        "--markdown",
        default=None,
        help=(
            "Also write a friend-shareable markdown rendering to this path. "
            "Skips rendering if the workflow's EvalReport was rejected."
        ),
    )

    render = subparsers.add_parser(
        "render",
        help="Render a completed Audit as friend-shareable markdown.",
    )
    render.add_argument(
        "--db",
        default="audit.db",
        help="SQLite path the Audit was written to (default: audit.db).",
    )
    render.add_argument(
        "--workflow-run-id",
        default=None,
        help="UUID of the run to render. If omitted, renders the most recent succeeded run.",
    )
    render.add_argument(
        "--output",
        default="-",
        help="Path to write the markdown file. Use '-' for stdout (default).",
    )

    history = subparsers.add_parser(
        "history",
        help="List all audit runs in the database.",
    )
    history.add_argument(
        "--db",
        default="audit.db",
        help="SQLite path (default: audit.db).",
    )
    history.add_argument(
        "--tenant",
        default=None,
        help="Filter by tenant ID (default: show all).",
    )

    reflect = subparsers.add_parser(
        "reflect",
        help="Run a continuation audit after a 30-day bet cycle.",
    )
    reflect.add_argument(
        "--db",
        default="audit.db",
        help="SQLite path (default: audit.db).",
    )
    outcome_grp = reflect.add_mutually_exclusive_group(required=True)
    outcome_grp.add_argument(
        "--outcome",
        default=None,
        help="Path to a structured OutcomeReport JSON file.",
    )
    outcome_grp.add_argument(
        "--outcome-text",
        default=None,
        help="Free-text owner reflection (triggers outcome_parser_agent).",
    )
    reflect.add_argument(
        "--workflow-run-id",
        default=None,
        help="UUID of the prior cycle to reflect on. Defaults to most recent succeeded run.",
    )
    reflect.add_argument(
        "--new-intake",
        default=None,
        help="Path to a new AuditIntake JSON if the business has changed.",
    )
    reflect.add_argument(
        "--output",
        default="-",
        help="Path to write the reflection report JSON. Use '-' for stdout.",
    )
    reflect.add_argument(
        "--markdown",
        default=None,
        help="Also write a friend-shareable markdown rendering to this path.",
    )

    return parser


def _build_provider() -> object | None:
    """Construct the LLMProvider chosen by env. Returns None on misconfiguration."""
    choice = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    model_override = os.environ.get("LLM_MODEL")

    if choice == "anthropic":
        from leverage_platform.llm import AnthropicProvider

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(
                "ANTHROPIC_API_KEY env var is required for LLM_PROVIDER=anthropic.",
                file=sys.stderr,
            )
            return None
        kwargs: dict[str, str] = {"api_key": api_key}
        if model_override:
            kwargs["default_model"] = model_override
        return AnthropicProvider(**kwargs)

    if choice == "openai":
        from leverage_platform.llm import OpenAIProvider

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "OPENAI_API_KEY env var is required for LLM_PROVIDER=openai.",
                file=sys.stderr,
            )
            return None
        kwargs2: dict[str, str] = {"api_key": api_key}
        if model_override:
            kwargs2["default_model"] = model_override
        return OpenAIProvider(**kwargs2)

    print(
        f"Unknown LLM_PROVIDER={choice!r}. Expected 'anthropic' or 'openai'.",
        file=sys.stderr,
    )
    return None


def _run_audit(intake_path: str, output_path: str, markdown_path: str | None) -> int:
    from leverage_platform.runtime import AgentContext
    from leverage_platform.storage import SQLiteStore

    from ai_leverage_audit.schemas import AuditIntake
    from ai_leverage_audit.workflow import run_audit

    intake_file = Path(intake_path)
    if not intake_file.exists():
        print(f"intake file not found: {intake_path}", file=sys.stderr)
        return 2

    raw = json.loads(intake_file.read_text())
    intake = AuditIntake.model_validate(raw)

    provider = _build_provider()
    if provider is None:
        return 2

    db_path = os.environ.get("AUDIT_DB", "audit.db")
    store = SQLiteStore(db_path)

    try:
        ctx = AgentContext(
            tenant_id=os.environ.get("AUDIT_TENANT_ID", "default"),
            provider=provider,
            store=store,
        )
        workflow_id, report = asyncio.run(run_audit(ctx, intake))

        out = {
            "workflow_run_id": str(workflow_id),
            "eval_report": report.model_dump(mode="json"),
        }
        rendered_json = json.dumps(out, indent=2)

        if output_path == "-":
            print(rendered_json)
        else:
            Path(output_path).write_text(rendered_json)
            print(f"audit report written to {output_path}", file=sys.stderr)

        if markdown_path:
            if report.accepted:
                from ai_leverage_audit.render import render_from_db, write_rendered

                md = render_from_db(db_path, workflow_run_id=workflow_id)
                write_rendered(md, markdown_path)
                if markdown_path != "-":
                    print(f"audit rendered to {markdown_path}", file=sys.stderr)
            else:
                print(
                    "skipping markdown render — EvalReport was rejected. "
                    "Inspect the JSON output for details.",
                    file=sys.stderr,
                )

        return 0 if report.accepted else 1
    finally:
        store.close()


def _render_audit_command(
    db_path: str, workflow_run_id: str | None, output_path: str
) -> int:
    from uuid import UUID

    from ai_leverage_audit.render import render_from_db, write_rendered

    if not Path(db_path).exists():
        print(f"audit db not found: {db_path}", file=sys.stderr)
        return 2

    try:
        run_id = UUID(workflow_run_id) if workflow_run_id else None
        content = render_from_db(db_path, workflow_run_id=run_id)
    except ValueError as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 2

    write_rendered(content, output_path)
    if output_path != "-":
        print(f"audit rendered to {output_path}", file=sys.stderr)
    return 0


def _history_command(db_path: str, tenant: str | None) -> int:
    import sqlite3

    if not Path(db_path).exists():
        print(f"audit db not found: {db_path}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, started_at, status FROM workflow_run ORDER BY started_at DESC"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No audit runs found.", file=sys.stderr)
        return 0

    col_w = max(len(str(r["id"])) for r in rows)
    print(f"{'RUN ID':<{col_w}}  {'STARTED AT':<26}  STATUS")
    print("-" * (col_w + 38))
    for r in rows:
        print(f"{r['id']:<{col_w}}  {r['started_at']:<26}  {r['status']}")
    return 0


def _reflect_command(
    db_path: str,
    outcome_path: str | None,
    outcome_text: str | None,
    workflow_run_id: str | None,
    new_intake_path: str | None,
    output_path: str,
    markdown_path: str | None,
) -> int:
    import json as _json

    from leverage_platform.runtime import AgentContext
    from leverage_platform.storage import SQLiteStore

    from ai_leverage_audit.render import load_state_from_db, render_from_db, write_rendered
    from ai_leverage_audit.schemas import AuditIntake, OutcomeReport
    from ai_leverage_audit.workflow import run_reflection

    if not Path(db_path).exists():
        print(f"audit db not found: {db_path}", file=sys.stderr)
        return 2

    from uuid import UUID
    prior_run_id = UUID(workflow_run_id) if workflow_run_id else None
    try:
        prior_state = load_state_from_db(db_path, workflow_run_id=prior_run_id)
    except ValueError as exc:
        print(f"could not load prior audit: {exc}", file=sys.stderr)
        return 2

    prior_parsed = prior_state["parsed_intake"]
    prior_workflow_map = prior_state["workflow_map"]
    prior_playbook = prior_state["first_playbook"]

    provider = _build_provider()
    if provider is None:
        return 2

    store = SQLiteStore(db_path)
    try:
        ctx = AgentContext(
            tenant_id=os.environ.get("AUDIT_TENANT_ID", "default"),
            provider=provider,
            store=store,
        )

        if outcome_path:
            raw_outcome = _json.loads(Path(outcome_path).read_text())
            outcome_report = OutcomeReport.model_validate(raw_outcome)
        else:
            from ai_leverage_audit.agents import outcome_parser_agent
            prior_bet = prior_state["thirty_day_bet"]
            outcome_report = asyncio.run(
                outcome_parser_agent(ctx, prior_bet, outcome_text)  # type: ignore[arg-type]
            )

        new_intake = None
        if new_intake_path:
            raw_intake = _json.loads(Path(new_intake_path).read_text())
            new_intake = AuditIntake.model_validate(raw_intake)

        workflow_id, report = asyncio.run(
            run_reflection(
                ctx,
                outcome_report,
                prior_parsed,  # type: ignore[arg-type]
                prior_workflow_map,  # type: ignore[arg-type]
                prior_playbook,  # type: ignore[arg-type]
                new_intake=new_intake,
            )
        )

        out = {
            "workflow_run_id": str(workflow_id),
            "eval_report": report.model_dump(mode="json"),
        }
        rendered_json = _json.dumps(out, indent=2)

        if output_path == "-":
            print(rendered_json)
        else:
            Path(output_path).write_text(rendered_json)
            print(f"reflection report written to {output_path}", file=sys.stderr)

        if markdown_path:
            if report.accepted:
                md = render_from_db(db_path, workflow_run_id=workflow_id)
                write_rendered(md, markdown_path)
                if markdown_path != "-":
                    print(f"reflection rendered to {markdown_path}", file=sys.stderr)
            else:
                print(
                    "skipping markdown render — EvalReport was rejected. "
                    "Inspect the JSON output for details.",
                    file=sys.stderr,
                )

        return 0 if report.accepted else 1
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_audit(args.intake, args.output, args.markdown)

    if args.command == "render":
        return _render_audit_command(args.db, args.workflow_run_id, args.output)

    if args.command == "history":
        return _history_command(args.db, args.tenant)

    if args.command == "reflect":
        return _reflect_command(
            args.db,
            args.outcome,
            args.outcome_text,
            args.workflow_run_id,
            args.new_intake,
            args.output,
            args.markdown,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

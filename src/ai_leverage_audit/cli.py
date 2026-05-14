"""Command-line entry point for the AI Leverage Audit.

`audit run --intake <path>` runs the full Audit workflow on a JSON intake
and writes the report (as JSON) to stdout or to `--output`.

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


def _run_audit(intake_path: str, output_path: str) -> int:
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

    store = SQLiteStore(os.environ.get("AUDIT_DB", "audit.db"))

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
        rendered = json.dumps(out, indent=2)

        if output_path == "-":
            print(rendered)
        else:
            Path(output_path).write_text(rendered)
            print(f"audit report written to {output_path}", file=sys.stderr)

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_audit(args.intake, args.output)

    if args.command == "render":
        return _render_audit_command(args.db, args.workflow_run_id, args.output)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

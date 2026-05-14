"""Command-line entry point for the AI Leverage Audit.

`audit run --intake <path>` runs the full Audit workflow on a JSON intake
and writes the report (as JSON) to stdout or to `--output`.

Environment variables consumed at runtime:
- ANTHROPIC_API_KEY: required for the Anthropic provider.
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

    return parser


def _run_audit(intake_path: str, output_path: str) -> int:
    from leverage_platform.llm import AnthropicProvider
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

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY env var is required for `audit run`.", file=sys.stderr)
        return 2

    provider = AnthropicProvider(api_key=api_key)
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_audit(args.intake, args.output)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

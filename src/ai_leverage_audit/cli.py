"""Command-line entry point for the AI Leverage Audit.

Gate 1 (current): `audit --help` works; `audit run` is a placeholder.
Gate 2 will wire `audit run --intake <path>` through the full Audit
workflow defined in PRODUCT_MVP.md §4.
"""

from __future__ import annotations

import argparse
import sys

from ai_leverage_audit import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit",
        description=(
            "AI Leverage Audit — diagnoses business workflows, scores AI "
            "leverage, designs a 30-day experiment. V1 is a one-shot CLI; "
            "see PRODUCT_VISION.md and PRODUCT_MVP.md in the leverage-platform "
            "repo for the full spec."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"audit {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    run = subparsers.add_parser(
        "run",
        help="Run the Audit on an intake JSON file (Gate 2 — not yet implemented).",
    )
    run.add_argument("--intake", required=True, help="Path to intake JSON file.")
    run.add_argument(
        "--output",
        default="-",
        help="Path to write the Audit report JSON. Use '-' for stdout (default).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        print(
            "audit run: not yet implemented (Gate 2). "
            "See PRODUCT_ROADMAP.md in the leverage-platform repo.",
            file=sys.stderr,
        )
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

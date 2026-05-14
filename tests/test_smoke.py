"""Smoke tests — proves the product package imports, the CLI runs, and the
sibling `leverage-platform` package is reachable.

Now that leverage-platform is a public repo and pinned as a regular
dependency (see pyproject.toml), the platform import is no longer
optional. CI must satisfy it before Gate 2 work begins.
"""

from __future__ import annotations

import pytest

import ai_leverage_audit
from ai_leverage_audit.cli import build_parser, main


def test_package_imports() -> None:
    """The product package itself imports cleanly."""
    assert ai_leverage_audit.__version__ == "0.0.0"


def test_cli_parser_builds() -> None:
    """argparse setup doesn't blow up at construction."""
    parser = build_parser()
    assert parser.prog == "audit"


def test_cli_no_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    """`audit` with no subcommand prints usage and exits 0."""
    rc = main([])
    assert rc == 0
    captured = capsys.readouterr()
    assert "AI Leverage Audit" in captured.out
    assert "run" in captured.out  # subcommand listed


def test_cli_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """`audit --help` prints usage and SystemExits 0 (argparse convention)."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "AI Leverage Audit" in captured.out


def test_cli_run_subcommand_is_placeholder(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`audit run --intake X` returns rc=1 with a 'not implemented' message."""
    rc = main(["run", "--intake", "fixtures/intakes/none.json"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not yet implemented" in captured.err


def test_leverage_platform_is_importable() -> None:
    """leverage-platform is a required dependency; the import must work."""
    import leverage_platform  # noqa: F401 — import-side-effects-only assertion

    # Smoke-check that a representative platform symbol resolves.
    from leverage_platform.runtime import agent  # noqa: F401

"""Gate 1 smoke tests — proves the product package imports and the CLI runs.

Platform integration (importing `leverage_platform.*`) is verified at Gate 2,
where the first real e2e test introduces a real workflow. The split is
deliberate: Gate 1 catches packaging and CLI-wiring issues without needing
CI access to the private leverage-platform repo. See README.md.
"""

from __future__ import annotations

import importlib.util

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


def test_leverage_platform_optional_at_gate_1() -> None:
    """leverage-platform may or may not be installed at Gate 1.

    Locally (with `uv sync --extra platform`) it is, and the import works.
    In CI (Gate 1) the extra is skipped — see README.md. Gate 2 makes it
    mandatory.
    """
    spec = importlib.util.find_spec("leverage_platform")
    if spec is None:
        pytest.skip(
            "leverage_platform not installed; expected in CI at Gate 1. "
            "Run `uv sync --extra platform` for local platform integration."
        )
    import leverage_platform  # noqa: F401 — import-side-effects-only assertion

    # If we got here, the platform imported. Smoke-check one symbol exists.
    from leverage_platform.runtime import agent  # noqa: F401

"""Parametrized schema regression test over the committed sample intakes.

For each `fixtures/intakes/samples/*.json`, assert it parses cleanly as an
`AuditIntake`. Catches schema drift instantly without spending LLM tokens —
the heavy "does the audit actually produce something useful?" question is
exercised by the live e2e test (gated on `RUN_LIVE_TESTS=1`).

When you commit a new sample, this test picks it up automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_leverage_audit.schemas import AuditIntake

SAMPLES_DIR = Path(__file__).parent.parent / "fixtures" / "intakes" / "samples"


def _sample_paths() -> list[Path]:
    return sorted(SAMPLES_DIR.glob("*.json"))


def test_samples_dir_exists() -> None:
    """The samples dir should exist — without it, the parametrized test would
    silently skip (zero params)."""
    assert SAMPLES_DIR.is_dir(), f"missing {SAMPLES_DIR}"


def test_at_least_five_sample_shapes_committed() -> None:
    """Gate 3 acceptance ('≥3 of 5 accepted') referenced 5 distinct shapes.
    We have more — but ≥5 is the floor."""
    paths = _sample_paths()
    assert len(paths) >= 5, (
        f"only {len(paths)} sample intakes; Gate 3 needs at least 5 distinct shapes."
    )


@pytest.fixture(params=_sample_paths(), ids=lambda p: p.stem)
def sample_path(request: pytest.FixtureRequest) -> Path:
    return request.param


def test_sample_loads_as_audit_intake(sample_path: Path) -> None:
    """Each committed sample parses without ValidationError."""
    raw = json.loads(sample_path.read_text())
    intake = AuditIntake.model_validate(raw)

    # Basic sanity — these would have triggered ValidationError already,
    # but the explicit asserts make the failure message friendlier.
    assert intake.business_type
    assert intake.current_role
    assert intake.team_size >= 1
    assert intake.months_in_business >= 0
    assert intake.weekly_time_to_invest_hours >= 1
    assert intake.monthly_budget_usd >= 0


def test_sample_has_distinct_free_text_fields(sample_path: Path) -> None:
    """Free-text fields should each be meaningfully populated — not just
    >= 30 chars (the schema floor) but also distinct enough to give the
    parser something to extract."""
    raw = json.loads(sample_path.read_text())
    intake = AuditIntake.model_validate(raw)

    fields = [
        intake.weekly_tasks_text,
        intake.current_tools_text,
        intake.top_time_sinks_text,
        intake.error_sensitive_areas_text,
        intake.customer_facing_areas_text,
        intake.primary_goal_text,
    ]
    # All six should be unique strings — copy-paste between fields is a
    # common authoring mistake (one of our earlier real intakes had it).
    assert len(set(fields)) == len(fields), (
        f"duplicate free-text fields in {sample_path.name} — "
        "owner likely copy-pasted between intake sections"
    )

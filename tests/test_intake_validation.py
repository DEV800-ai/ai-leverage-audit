"""Intake validation tests — PRODUCT_MVP.md §2 invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_leverage_audit.schemas import AuditIntake, BaselineMeasurement, ParsedIntake


def _good_intake_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "business_type": "freelance designer",
        "current_role": "owner-operator",
        "team_size": 1,
        "months_in_business": 12,
        "weekly_tasks_text": "a" * 50,
        "current_tools_text": "b" * 50,
        "top_time_sinks_text": "c" * 50,
        "error_sensitive_areas_text": "d" * 50,
        "customer_facing_areas_text": "e" * 50,
        "primary_goal_text": "f" * 50,
        "weekly_time_to_invest_hours": 8,
        "monthly_budget_usd": 100,
        "things_owner_refuses_to_automate_text": None,
    }
    base.update(overrides)
    return base


def test_valid_intake_accepted() -> None:
    intake = AuditIntake.model_validate(_good_intake_kwargs())
    assert intake.business_type == "freelance designer"


def test_free_text_field_too_short_rejected() -> None:
    with pytest.raises(ValidationError, match="weekly_tasks_text"):
        AuditIntake.model_validate(_good_intake_kwargs(weekly_tasks_text="short"))


def test_weekly_time_below_one_rejected() -> None:
    with pytest.raises(ValidationError, match="weekly_time_to_invest_hours"):
        AuditIntake.model_validate(_good_intake_kwargs(weekly_time_to_invest_hours=0))


def test_weekly_time_above_forty_rejected() -> None:
    with pytest.raises(ValidationError, match="weekly_time_to_invest_hours"):
        AuditIntake.model_validate(_good_intake_kwargs(weekly_time_to_invest_hours=41))


def test_team_size_zero_rejected() -> None:
    with pytest.raises(ValidationError, match="team_size"):
        AuditIntake.model_validate(_good_intake_kwargs(team_size=0))


def test_negative_budget_rejected() -> None:
    with pytest.raises(ValidationError, match="monthly_budget_usd"):
        AuditIntake.model_validate(_good_intake_kwargs(monthly_budget_usd=-1))


def test_extra_field_rejected() -> None:
    """`extra="forbid"` keeps the intake schema honest about its surface."""
    with pytest.raises(ValidationError, match="extra"):
        AuditIntake.model_validate(_good_intake_kwargs(unknown_field="x"))


def test_refused_automation_field_optional() -> None:
    """Owners are allowed to skip the refused-automation field."""
    intake = AuditIntake.model_validate(
        _good_intake_kwargs(things_owner_refuses_to_automate_text=None)
    )
    assert intake.things_owner_refuses_to_automate_text is None


def test_measurement_context_text_optional() -> None:
    """measurement_context_text is optional — existing intakes without it stay valid."""
    intake = AuditIntake.model_validate(_good_intake_kwargs())
    assert intake.measurement_context_text is None


def test_measurement_context_text_accepted() -> None:
    intake = AuditIntake.model_validate(
        _good_intake_kwargs(measurement_context_text="Invoice processing: 3/week, 30 min each.")
    )
    assert intake.measurement_context_text is not None


def test_baseline_measurement_partial_fields_valid() -> None:
    """BaselineMeasurement accepts partial data — owner may answer only some questions."""
    bm = BaselineMeasurement(task_or_workflow_ref="invoice processing", minutes_per_unit=30.0)
    assert bm.volume_per_week is None
    assert bm.minutes_per_unit == 30.0


def test_baseline_measurement_pct_bounds() -> None:
    with pytest.raises(ValidationError):
        BaselineMeasurement(task_or_workflow_ref="x", mechanical_pct=101)
    with pytest.raises(ValidationError):
        BaselineMeasurement(task_or_workflow_ref="x", owner_review_pct_if_assisted=-1)


def test_parsed_intake_baseline_defaults_empty() -> None:
    """ParsedIntake.baseline_measurements defaults to [] when not supplied."""
    pi = ParsedIntake(
        business_summary="test",
        weekly_tasks=[
            {"title": "t1", "estimated_time_minutes_per_week": 60,
             "is_customer_facing": False, "is_error_sensitive": False},
            {"title": "t2", "estimated_time_minutes_per_week": 30,
             "is_customer_facing": False, "is_error_sensitive": False},
            {"title": "t3", "estimated_time_minutes_per_week": 20,
             "is_customer_facing": False, "is_error_sensitive": False},
        ],
        tools_in_use=[],
        top_pain_points=[],
        primary_goal="save time",
        weekly_time_budget_hours=5,
        monthly_budget_usd=50,
        refused_automation_areas=[],
    )
    assert pi.baseline_measurements == []

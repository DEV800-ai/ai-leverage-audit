"""Pydantic schemas for the AI Leverage Audit V1.

Spec: docs/product/PRODUCT_MVP.md §3 in the leverage-platform repo.

All output artifacts get `schema_name = "<Name>@v1"` when persisted via
the platform's Artifact primitive (ADR-004).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------- Intake ----------


class AuditIntake(BaseModel):
    """Raw owner-supplied intake. V1 prefers free-text over dropdowns;
    the parser agent extracts structure."""

    model_config = ConfigDict(extra="forbid")

    business_type: str
    current_role: str
    team_size: int = Field(ge=1)
    months_in_business: int = Field(ge=0)

    weekly_tasks_text: str = Field(min_length=30)
    current_tools_text: str = Field(min_length=30)
    top_time_sinks_text: str = Field(min_length=30)
    error_sensitive_areas_text: str = Field(min_length=30)
    customer_facing_areas_text: str = Field(min_length=30)

    primary_goal_text: str = Field(min_length=30)
    weekly_time_to_invest_hours: int = Field(ge=1, le=40)
    monthly_budget_usd: int = Field(ge=0)
    things_owner_refuses_to_automate_text: str | None = None


# ---------- Parsed Intake ----------


class WeeklyTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    estimated_time_minutes_per_week: int = Field(ge=0)
    is_customer_facing: bool
    is_error_sensitive: bool
    current_tool: str | None = None


class ParsedIntake(BaseModel):
    """Structured representation of the AuditIntake, produced by the parser."""

    model_config = ConfigDict(extra="forbid")

    business_summary: str
    weekly_tasks: list[WeeklyTask] = Field(min_length=3, max_length=15)
    tools_in_use: list[str]
    top_pain_points: list[str] = Field(max_length=5)
    primary_goal: str
    weekly_time_budget_hours: int = Field(ge=1, le=40)
    monthly_budget_usd: int = Field(ge=0)
    refused_automation_areas: list[str]


# ---------- Workflow Map ----------


class Workflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    title: str
    description: str
    frequency: Literal["daily", "weekly", "monthly", "event_driven"]
    # Allow fractional values: a monthly workflow is ~0.25 occurrences/week.
    # Floor at 0 so event-driven workflows can express rarity (e.g. 0.1).
    minutes_per_occurrence: float = Field(ge=0)
    occurrences_per_week: float = Field(ge=0)
    inputs: str
    outputs: str
    pain_points: list[str]
    tools_used: list[str]


class WorkflowMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflows: list[Workflow] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def _unique_workflow_ids(self) -> WorkflowMap:
        ids = [w.id for w in self.workflows]
        if len(ids) != len(set(ids)):
            raise ValueError("workflow ids must be unique within a WorkflowMap")
        return self


# ---------- Leverage Analysis ----------


class WorkflowLeverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str

    time_saved_hours_per_week_estimate: float = Field(ge=0)
    risk_if_ai_gets_it_wrong: Literal["low", "medium", "high"]
    setup_complexity: Literal["low", "medium", "high"]
    human_judgment_needed: Literal["low", "medium", "high"]
    rank: int = Field(ge=1)
    rationale: str

    automate_pct: int = Field(ge=0, le=100)
    assist_pct: int = Field(ge=0, le=100)
    keep_human_pct: int = Field(ge=0, le=100)
    automate_examples: list[str]
    assist_examples: list[str]
    keep_human_examples: list[str]

    # Honesty fields — optional for backwards compatibility with audits
    # rendered before they were added. Older audit.db rows still validate.
    # The leverage_analyst prompt instructs the LLM to populate them; when
    # populated, the renderer surfaces them so the owner sees explicit
    # uncertainty instead of false precision.
    confidence: Literal["low", "medium", "high"] | None = None
    evidence_from_intake: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_pct_sum_and_examples(self) -> WorkflowLeverage:
        total = self.automate_pct + self.assist_pct + self.keep_human_pct
        if total != 100:
            raise ValueError(
                f"automate_pct + assist_pct + keep_human_pct must sum to 100, got {total}"
            )
        if self.automate_pct > 0 and not self.automate_examples:
            raise ValueError("automate_examples required when automate_pct > 0")
        if self.assist_pct > 0 and not self.assist_examples:
            raise ValueError("assist_examples required when assist_pct > 0")
        if self.keep_human_pct > 0 and not self.keep_human_examples:
            raise ValueError("keep_human_examples required when keep_human_pct > 0")
        return self


class LeverageAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    per_workflow: list[WorkflowLeverage]
    overall_top_three_ids: list[str] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def _ranks_and_top_three(self) -> LeverageAnalysis:
        ranks = sorted(w.rank for w in self.per_workflow)
        expected = list(range(1, len(ranks) + 1))
        if ranks != expected:
            raise ValueError(
                f"ranks must be a permutation of 1..N, got {ranks} (expected {expected})"
            )
        top_three_from_ranks = {w.workflow_id for w in self.per_workflow if w.rank <= 3}
        if set(self.overall_top_three_ids) != top_three_from_ranks:
            raise ValueError(
                f"overall_top_three_ids {self.overall_top_three_ids} "
                f"must match ranks 1-3 {sorted(top_three_from_ranks)}"
            )
        return self


# ---------- 30-Day Bet ----------


class ThirtyDayBet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_workflow_id: str
    title: str
    hypothesis: str
    success_metric: str
    failure_metric: str
    weekly_plan: list[str] = Field(min_length=4, max_length=4)
    first_48h_actions: list[str] = Field(min_length=2)
    expected_asset_created: str
    estimated_weekly_time_hours: int = Field(ge=1)
    estimated_setup_cost_usd: int = Field(ge=0)

    @model_validator(mode="after")
    def _success_and_failure_differ(self) -> ThirtyDayBet:
        if self.success_metric.strip() == self.failure_metric.strip():
            raise ValueError(
                "success_metric and failure_metric must differ (identical strings)"
            )
        return self


# ---------- Risk and Agency Map ----------


class KeepHumanArea(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: str
    reason: str
    severity: Literal["low", "medium", "high"]


class AutomationRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automation: str
    what_could_break: str
    mitigation: str


class AgencyCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trigger: str
    required_action: str
    cadence: Literal["per_event", "daily", "weekly", "monthly"] | None = None


class RiskAndAgencyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keep_human_areas: list[KeepHumanArea] = Field(min_length=2)
    automation_risks: list[AutomationRisk] = Field(min_length=2)
    agency_checkpoints: list[AgencyCheckpoint] = Field(min_length=3)
    weekly_review_questions: list[str] = Field(min_length=3, max_length=6)
    compliance_or_legal_flags: list[str]


# ---------- First Playbook ----------


class PlaybookEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    current_status: Literal[
        "not_yet_tested", "experimenting", "validated", "rejected"
    ]
    summary: str


class FirstPlaybook(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    business_summary: str
    workflow_entries: list[PlaybookEntry]
    rules_for_human_involvement: list[str] = Field(min_length=3)
    open_questions: list[str]
    next_review_offset_days: int = Field(ge=1, default=30)

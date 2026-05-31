"""Minimal FastAPI mock that returns a pre-baked AuditResponse fixture.

Used by E2E tests so the browser-facing Next.js app has something to talk to
without spending real LLM tokens.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

FIXTURE_RUN_ID = "00000000-0000-0000-0000-000000000042"

_BET = {
    "target_workflow_id": "customer_support",
    "title": "Automate FAQ replies with AI",
    "hypothesis": (
        "If we use AI to draft answers to the top 5 support questions, "
        "weekly support time drops from 5 h to under 1 h within 30 days."
    ),
    "success_metric": "Support time < 1 h/week for 3 consecutive weeks.",
    "failure_metric": "Support time > 4 h/week or a customer complaint in week 2+.",
    "weekly_plan": [
        "Week 1: Catalogue top 10 FAQ questions and draft AI template answers.",
        "Week 2: Run AI drafts on real incoming emails; human reviews each reply.",
        "Week 3: Reduce human review to spot-checks on 20 % of replies.",
        "Week 4: Measure time saved vs baseline.",
    ],
    "first_48h_actions": [
        "Export last 30 days of support emails and tag the top 5 question types.",
        "Create a shared doc with template answers for each question type.",
    ],
    "expected_asset_created": "AI-assisted FAQ reply system handling 70 % of support volume.",
    "estimated_weekly_time_hours": 3.0,
    "estimated_setup_cost_usd": 50,
}

_RISK = {
    "keep_human_areas": [
        {
            "area": "Refund and billing decisions",
            "reason": "Financially irreversible; errors damage trust.",
            "severity": "high",
        }
    ],
    "automation_risks": [
        {
            "automation": "AI FAQ drafts",
            "what_could_break": "Misreads an unusual or emotional query.",
            "mitigation": "Human fallback for any reply flagged uncertain by the model.",
        }
    ],
    "agency_checkpoints": [
        {
            "trigger": "Customer escalation or complaint",
            "required_action": "Pause AI drafts for that thread; respond personally.",
            "cadence": "per_event",
        }
    ],
    "weekly_review_questions": [
        "Did the AI drafts match the brand voice this week?",
        "Any queries the AI handled badly?",
    ],
    "compliance_or_legal_flags": [],
}

_PLAYBOOK = {
    "title": "AI Leverage Playbook — Cycle 1",
    "business_summary": "Solo consulting practice; owner handles all client comms and delivery.",
    "workflow_entries": [
        {
            "workflow_id": "customer_support",
            "current_status": "not_yet_tested",
            "summary": "Handle FAQ emails with AI-drafted replies.",
            "cycle_introduced": 1,
            "last_outcome_summary": None,
        }
    ],
    "rules_for_human_involvement": [
        "Always review refund or billing replies before sending.",
        "Personally handle any emotionally charged messages.",
    ],
    "open_questions": [
        "What email volume threshold should trigger a human-only week?",
    ],
    "next_review_offset_days": 30,
    "cycle_number": 1,
}

FIXTURE_RESPONSE = {
    "workflow_run_id": FIXTURE_RUN_ID,
    "accepted": True,
    "summary": "Audit accepted. Strong leverage opportunity identified in customer support.",
    "markdown": (
        "# AI Leverage Audit\n\n"
        "## Your 30-Day Bet\n\n"
        "**Automate FAQ replies with AI** — target: support time < 1 h/week.\n\n"
        "## Workflow Map\n\n"
        "| Workflow | Time/week | AI-ready? |\n"
        "|---|---|---|\n"
        "| Customer support FAQ | 5 h | Yes |\n\n"
        "## Risk & Agency\n\n"
        "Keep humans in the loop for refund decisions.\n"
    ),
    "state": {
        "workflow_run_id": FIXTURE_RUN_ID,
        "thirty_day_bet": _BET,
        "risk_agency_map": _RISK,
        "first_playbook": _PLAYBOOK,
    },
}


def create_app() -> FastAPI:
    app = FastAPI(title="AI Leverage Audit — Mock API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/audit")
    async def run_audit(request: Request) -> dict:
        return FIXTURE_RESPONSE

    @app.get("/api/audit/{run_id}")
    def get_audit(run_id: str) -> dict:
        return FIXTURE_RESPONSE

    @app.get("/api/history")
    def get_history() -> list:
        return [
            {
                "workflow_run_id": FIXTURE_RUN_ID,
                "status": "succeeded",
                "started_at": "2026-05-26T10:00:00Z",
                "cycle_number": 1,
            }
        ]

    @app.post("/api/reflect")
    async def run_reflect(request: Request) -> dict:
        return FIXTURE_RESPONSE

    return app

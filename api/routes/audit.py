"""POST /api/audit — run a full audit and return the report.
POST /api/reflect — run a continuation audit.
GET  /api/audit/{workflow_run_id} — load a saved report.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_leverage_audit.render import load_state_from_db, render_audit_markdown
from ai_leverage_audit.schemas import AuditIntake, OutcomeReport
from ai_leverage_audit.workflow import run_audit, run_reflection
from api.deps import DB_PATH, get_ctx

router = APIRouter()


class AuditRequest(BaseModel):
    intake: AuditIntake


class ReflectRequest(BaseModel):
    outcome_report: OutcomeReport
    prior_workflow_run_id: str


class AuditResponse(BaseModel):
    workflow_run_id: str
    accepted: bool
    summary: str
    markdown: str
    state: dict[str, Any]


@router.post("/audit", response_model=AuditResponse)
async def run_audit_endpoint(body: AuditRequest) -> AuditResponse:
    ctx = get_ctx()
    try:
        workflow_id, report = await run_audit(ctx, body.intake)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    state = load_state_from_db(DB_PATH, workflow_run_id=str(workflow_id))
    md = render_audit_markdown(state) if report.accepted else ""

    return AuditResponse(
        workflow_run_id=str(workflow_id),
        accepted=report.accepted,
        summary=report.summary,
        markdown=md,
        state={k: v.model_dump() if hasattr(v, "model_dump") else v
               for k, v in state.items()},
    )


@router.post("/reflect", response_model=AuditResponse)
async def run_reflect_endpoint(body: ReflectRequest) -> AuditResponse:
    ctx = get_ctx()

    # Load prior cycle artifacts.
    try:
        prior_state = load_state_from_db(
            DB_PATH, workflow_run_id=body.prior_workflow_run_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    parsed = prior_state["parsed_intake"]
    workflow_map = prior_state["workflow_map"]
    prior_playbook = prior_state["first_playbook"]

    try:
        workflow_id, report = await run_reflection(
            ctx,
            body.outcome_report,
            parsed,
            workflow_map,
            prior_playbook,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    state = load_state_from_db(DB_PATH, workflow_run_id=str(workflow_id))
    md = render_audit_markdown(state) if report.accepted else ""

    return AuditResponse(
        workflow_run_id=str(workflow_id),
        accepted=report.accepted,
        summary=report.summary,
        markdown=md,
        state={k: v.model_dump() if hasattr(v, "model_dump") else v
               for k, v in state.items()},
    )


@router.get("/audit/{workflow_run_id}", response_model=AuditResponse)
def get_audit_endpoint(workflow_run_id: str) -> AuditResponse:
    try:
        UUID(workflow_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid UUID") from exc

    try:
        state = load_state_from_db(DB_PATH, workflow_run_id=workflow_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    md = render_audit_markdown(state)
    report = state.get("eval_report")

    return AuditResponse(
        workflow_run_id=workflow_run_id,
        accepted=report.accepted if report else False,
        summary=report.summary if report else "",
        markdown=md,
        state={k: v.model_dump() if hasattr(v, "model_dump") else v
               for k, v in state.items()},
    )

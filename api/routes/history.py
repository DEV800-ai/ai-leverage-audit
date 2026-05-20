"""GET /api/history — list past audit runs."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from api.deps import DB_PATH

router = APIRouter()


class RunSummary(BaseModel):
    workflow_run_id: str
    status: str
    started_at: str
    cycle_number: int | None = None


@router.get("/history", response_model=list[RunSummary])
def list_history() -> list[RunSummary]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, status, started_at FROM workflow_run ORDER BY started_at DESC"
        ).fetchall()

        results = []
        for row in rows:
            # Derive cycle number from artifact count if playbook artifact exists.
            cycle_row = conn.execute(
                "SELECT data FROM artifact "
                "WHERE workflow_run_id = ? AND type = 'first_playbook'",
                (row["id"],),
            ).fetchone()
            cycle = None
            if cycle_row:
                import json
                try:
                    cycle = json.loads(cycle_row["data"]).get("cycle_number", 1)
                except Exception:
                    cycle = 1
            results.append(RunSummary(
                workflow_run_id=row["id"],
                status=row["status"],
                started_at=row["started_at"],
                cycle_number=cycle,
            ))

        conn.close()
        return results
    except Exception:
        return []

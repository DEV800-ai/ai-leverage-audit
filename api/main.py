"""FastAPI entry point — AI Leverage Audit API."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.audit import router as audit_router
from api.routes.history import router as history_router

app = FastAPI(
    title="AI Leverage Audit API",
    description="Diagnose → Test → Evolve for solopreneurs and small businesses.",
    version="0.1.0",
)

# Allow Next.js dev server and production origin.
origins = [
    "http://localhost:3000",
    os.environ.get("WEB_ORIGIN", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

"""Shared FastAPI dependencies — LLM provider, store, AgentContext."""

from __future__ import annotations

import os

from leverage_platform.runtime import AgentContext
from leverage_platform.storage import SQLiteStore

from ai_leverage_audit.cli import _build_provider  # reuse CLI provider builder

DB_PATH = os.environ.get("AUDIT_DB", "audit.db")


def get_store() -> SQLiteStore:
    return SQLiteStore(DB_PATH)


TENANT_ID = os.environ.get("AUDIT_TENANT_ID", "default")


def get_ctx() -> AgentContext:
    provider = _build_provider()
    store = get_store()
    return AgentContext(tenant_id=TENANT_ID, provider=provider, store=store)

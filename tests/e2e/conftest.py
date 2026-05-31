"""Session-scoped fixtures for E2E browser tests.

Starts two servers once per pytest session:
  1. Mock FastAPI on MOCK_API_PORT (returns fixture AuditResponse, no LLM calls).
  2. Next.js dev server on NEXT_PORT, with NEXT_PUBLIC_API_URL pointing at the mock.

Set E2E_BASE_URL to skip launching a new Next.js instance and reuse one already running
(e.g. `E2E_BASE_URL=http://localhost:3000 pytest tests/e2e`).
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import uvicorn

from tests.e2e.mock_api import create_app

MOCK_API_PORT = 18000
NEXT_PORT = 13000
WEB_DIR = Path(__file__).parent.parent.parent / "web"


# ---------------------------------------------------------------------------
# Mock API server
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mock_api_server() -> str:
    """Start the FastAPI mock on MOCK_API_PORT; yield its base URL."""
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=MOCK_API_PORT, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    _wait_for_url(f"http://127.0.0.1:{MOCK_API_PORT}/health", timeout=10)
    yield f"http://127.0.0.1:{MOCK_API_PORT}"
    server.should_exit = True
    thread.join(timeout=5)


# ---------------------------------------------------------------------------
# Next.js dev server
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def next_server(mock_api_server: str) -> str:
    """Start Next.js dev server; yield its base URL.

    Skipped when E2E_BASE_URL is set in the environment — the caller's
    already-running instance is used instead.
    """
    override = os.environ.get("E2E_BASE_URL")
    if override:
        yield override
        return

    env = {**os.environ, "NEXT_PUBLIC_API_URL": mock_api_server}

    proc = subprocess.Popen(
        ["node_modules/.bin/next", "dev", "-p", str(NEXT_PORT)],
        cwd=WEB_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_url(f"http://localhost:{NEXT_PORT}", timeout=60)
        yield f"http://localhost:{NEXT_PORT}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


# ---------------------------------------------------------------------------
# pytest-playwright base_url override
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def base_url(next_server: str) -> str:
    """Override pytest-playwright's base_url with our Next.js server URL."""
    return next_server


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _wait_for_url(url: str, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)  # noqa: S310
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(0.25)
    raise RuntimeError(f"Server at {url} did not become ready within {timeout}s") from last_exc

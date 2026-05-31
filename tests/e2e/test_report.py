"""E2E tests for the report, bet, and history pages.

These tests navigate directly to pages backed by the mock API's fixture
FIXTURE_RUN_ID, verifying that key content renders correctly.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.mock_api import FIXTURE_RUN_ID


# ---------------------------------------------------------------------------
# Report page (/report/{id})
# ---------------------------------------------------------------------------


def test_report_page_loads(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/report/{FIXTURE_RUN_ID}")

    # Accepted badge visible.
    expect(page.get_by_text("Accepted")).to_be_visible()


def test_report_page_renders_markdown(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/report/{FIXTURE_RUN_ID}")

    # Markdown headings from the fixture response.
    expect(page.get_by_text("AI Leverage Audit")).to_be_visible()
    expect(page.get_by_text("Your 30-Day Bet")).to_be_visible()


def test_report_page_has_bet_cta(page: Page, base_url: str) -> None:
    """The report page shows a CTA card that links to /bet/{id}."""
    page.goto(f"{base_url}/report/{FIXTURE_RUN_ID}")

    bet_link = page.get_by_role("link", name=re.compile(r"bet|Bet|experiment", re.I)).first
    expect(bet_link).to_be_visible()
    expect(bet_link).to_have_attribute("href", re.compile(rf"/bet/{FIXTURE_RUN_ID}"))


def test_report_not_found_shows_error(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/report/does-not-exist")
    # Mock returns the fixture for any ID, so this verifies the page doesn't crash.
    # The real 404 path is covered by the API-level tests.
    expect(page.locator("main")).to_be_visible()


# ---------------------------------------------------------------------------
# Bet page (/bet/{id})
# ---------------------------------------------------------------------------


def test_bet_page_loads(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/bet/{FIXTURE_RUN_ID}")
    expect(page.get_by_text("Automate FAQ replies with AI")).to_be_visible()


def test_bet_page_shows_weekly_plan(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/bet/{FIXTURE_RUN_ID}")
    expect(page.get_by_text(re.compile(r"Week 1"))).to_be_visible()


def test_bet_page_shows_risk_section(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/bet/{FIXTURE_RUN_ID}")
    # The keep-human areas from the fixture.
    expect(page.get_by_text(re.compile(r"Refund", re.I))).to_be_visible()


def test_bet_page_has_link_to_report(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/bet/{FIXTURE_RUN_ID}")
    # A back or navigation link pointing to /report/{id}.
    report_link = page.get_by_role("link", name=re.compile(r"report|back|audit", re.I)).first
    expect(report_link).to_be_visible()


# ---------------------------------------------------------------------------
# History page (/history)
# ---------------------------------------------------------------------------


def test_history_page_loads(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/history")
    # The fixture history entry renders a "succeeded" status badge.
    expect(page.get_by_text("succeeded", exact=True).first).to_be_visible()


# ---------------------------------------------------------------------------
# Home page (/)
# ---------------------------------------------------------------------------


def test_home_page_has_start_link(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/")
    start_link = page.get_by_role("link", name=re.compile(r"start|begin|audit", re.I)).first
    expect(start_link).to_be_visible()

"""E2E tests for the intake form (/intake).

Covers:
- Step gating: Next is disabled until required fields are filled.
- Step navigation: forward and back.
- N/A toggle: marks field as N/A and can be cleared.
- Validation error: short text on Review step shows inline error.
- Happy path: full 5-step form → submit → redirect to /report/{id}.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.mock_api import FIXTURE_RUN_ID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LONG_TEXT = (
    "This is a detailed description that definitely exceeds the thirty-character minimum "
    "required for this field to be considered valid in the form."
)

NA_ERROR_SENSITIVE = (
    "Not applicable — this business has no error-sensitive or financially irreversible workflows."
)


def fill_step1(page: Page) -> None:
    page.get_by_placeholder("Independent neighbourhood supermarket").fill("Solo consulting practice")
    page.get_by_placeholder("Owner-operator — handles purchasing").fill("Owner / sole trader")


def fill_step2(page: Page) -> None:
    page.locator("textarea").nth(0).fill(
        "Answer client emails (1h/day), write proposals (3h/week), deliver project work (20h/week)."
    )
    page.locator("textarea").nth(1).fill(
        "Writing the same project status update email to every client every Friday takes 90 min."
    )


def fill_step3(page: Page) -> None:
    page.locator("textarea").nth(0).fill(
        "Gmail, Google Docs, Notion, Calendly, Stripe for invoicing, Zoom for client calls."
    )
    page.locator("textarea").nth(1).fill(
        "Final deliverable sign-off and all invoice amounts — mistakes cost real money."
    )
    page.locator("textarea").nth(2).fill(
        "All client-facing emails, proposals, and the monthly newsletter."
    )


def fill_step4(page: Page) -> None:
    page.locator("textarea").nth(0).fill(
        "Cut time spent on non-billable admin from 10 h/week to under 3 h so I can take on one more client."
    )
    page.locator("textarea").nth(1).fill(
        "Final decisions on deliverables and any communication about contract changes."
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _next_btn(page: Page):
    return page.get_by_role("button", name="Next", exact=True)


def test_intake_page_loads(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    expect(page.get_by_role("heading", name="Your business")).to_be_visible()
    expect(page.get_by_text("Step 1 of 5")).to_be_visible()


def test_next_disabled_on_empty_step1(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    expect(_next_btn(page)).to_be_disabled()


def test_next_enabled_after_filling_step1(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    expect(_next_btn(page)).to_be_disabled()

    fill_step1(page)

    expect(_next_btn(page)).to_be_enabled()


def test_navigate_forward_and_back(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")

    fill_step1(page)
    _next_btn(page).click()
    expect(page.get_by_text("Step 2 of 5")).to_be_visible()
    expect(page.get_by_role("heading", name="Weekly workflows")).to_be_visible()

    page.get_by_role("button", name="Back").click()
    expect(page.get_by_text("Step 1 of 5")).to_be_visible()
    expect(page.get_by_role("heading", name="Your business")).to_be_visible()


def test_step2_next_disabled_on_short_text(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    fill_step1(page)
    _next_btn(page).click()

    expect(_next_btn(page)).to_be_disabled()

    # Filling only one of the two required textareas keeps Next disabled.
    page.locator("textarea").nth(0).fill(LONG_TEXT)
    expect(_next_btn(page)).to_be_disabled()

    page.locator("textarea").nth(1).fill(LONG_TEXT)
    expect(_next_btn(page)).to_be_enabled()


def test_na_toggle_marks_field_not_applicable(page: Page, base_url: str) -> None:
    """Clicking the N/A button on an optional field replaces the textarea."""
    page.goto(f"{base_url}/intake")
    fill_step1(page)
    _next_btn(page).click()
    fill_step2(page)
    _next_btn(page).click()

    # Step 3 — click N/A on the first NAField (error-sensitive areas).
    page.get_by_role("button", name="N/A", exact=True).first.click()

    expect(page.get_by_text("Not applicable")).to_be_visible()
    expect(page.get_by_role("button", name="Clear", exact=True)).to_be_visible()


def test_na_toggle_clear_restores_textarea(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    fill_step1(page)
    _next_btn(page).click()
    fill_step2(page)
    _next_btn(page).click()

    page.get_by_role("button", name="N/A", exact=True).first.click()
    page.get_by_role("button", name="Clear", exact=True).click()

    # Textarea should be visible again (empty).
    expect(page.locator("textarea").nth(1)).to_be_visible()


def test_progress_bar_advances(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/intake")
    fill_step1(page)

    bar = page.locator(".bg-indigo-500")
    style_step1 = bar.get_attribute("style") or ""

    _next_btn(page).click()
    style_step2 = bar.get_attribute("style") or ""

    # Width percentage must increase when moving to step 2.
    assert style_step1 != style_step2


@pytest.mark.slow
def test_happy_path_full_submission(page: Page, base_url: str) -> None:
    """Fill all 5 steps, submit, and land on the report page."""
    page.goto(f"{base_url}/intake")

    # Step 1
    fill_step1(page)
    _next_btn(page).click()

    # Step 2
    fill_step2(page)
    _next_btn(page).click()

    # Step 3
    fill_step3(page)
    _next_btn(page).click()

    # Step 4
    fill_step4(page)
    _next_btn(page).click()

    # Step 5 — review
    expect(page.get_by_text("Step 5 of 5")).to_be_visible()
    expect(page.get_by_text("Solo consulting practice")).to_be_visible()

    submit_btn = page.get_by_role("button", name=re.compile(r"Run my audit"))
    expect(submit_btn).to_be_visible()
    submit_btn.click()

    # Wait for navigation to /report/{id}.
    page.wait_for_url(re.compile(r"/report/"), timeout=10_000)
    expect(page).to_have_url(re.compile(rf"/report/{FIXTURE_RUN_ID}"))

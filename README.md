# ai-leverage-audit

> **AI Operating Mentor for solopreneurs and small business owners.** Diagnoses business workflows, identifies where AI creates real leverage, designs a 30-day experiment with success and failure metrics, and produces a first version of a business-specific playbook.

The full product spec lives in the [`leverage-platform`](https://github.com/DEV800-ai/leverage-platform) repo under `docs/product/`:

- [`PRODUCT_VISION.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_VISION.md) — positioning, market pain, MVP wedge.
- [`PRODUCT_MVP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_MVP.md) — V1 spec: intake schema, 7 output artifacts, agent workflow, success criteria, non-goals.
- [`PRODUCT_ROADMAP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_ROADMAP.md) — three gates to V1, evidence-gated V2 bets.

## Status

**Gate 2 — Synthetic Audit accepted.** All 7 agents, 7 schemas, prompts, 10 deterministic rules + 6-question rubric, and the workflow orchestration ship per [`PRODUCT_MVP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_MVP.md) §3–§6. The synthetic-consultant intake produces `EvalReport.accepted=true` end-to-end against `MockLLMProvider`. An opt-in live test exercises real Anthropic when `RUN_LIVE_TESTS=1` is set.

Next: **Gate 3** — 5 friend-and-family real intakes meet `PRODUCT_MVP.md` §7 acceptance.

### Running a live Audit — one command

```bash
LLM_PROVIDER=openai OPENAI_API_KEY=sk-... \
  uv run audit run \
    --intake fixtures/intakes/synthetic_consultant.json \
    --output report.json \
    --markdown report.md
```

Produces both outputs in one call. The JSON is the platform's full audit log; the markdown is friend-shareable (workflow map, top-3 leverage workflows, 30-day bet with success/failure metrics, keep-human areas, weekly review questions, day-0 playbook). If the audit's `EvalReport` is rejected, the markdown step is skipped — inspect the JSON to see which rules failed.

Anthropic works the same way (it's the default provider — drop `LLM_PROVIDER=openai` and use `ANTHROPIC_API_KEY` instead).

Optional env vars: `LLM_MODEL` overrides the provider default (e.g. `LLM_MODEL=gpt-4o-mini`), `AUDIT_DB` overrides the SQLite path, `AUDIT_TENANT_ID` overrides the tenant attribution string.

Intermediate artifacts (parsed intake, workflow map, leverage analysis, 30-day bet, risk + agency map, first playbook) are persisted as `Artifact` rows in `audit.db`.

### Re-rendering an older Audit

```bash
uv run audit render --db audit.db --output report.md
```

Renders the most recent succeeded run from the SQLite store. Pass `--workflow-run-id <uuid>` to pick a specific older run, or `--output -` to print to stdout. Useful when you want to regenerate the friend-shareable doc after iterating on the renderer.

## Local development

```bash
uv sync --extra dev          # installs leverage-platform from GitHub (public)
uv run audit --help
uv run pytest
```

Working against an in-progress sibling checkout of `leverage-platform`? After `uv sync`, override the GitHub-resolved version with a local editable install:

```bash
git clone git@github.com:DEV800-ai/leverage-platform.git ../leverage-platform
uv pip install -e ../leverage-platform
```

The product's smoke test imports `leverage_platform.runtime.agent` to confirm the sibling is reachable.

## CI

GitHub Actions runs ruff + pytest + uv build + `audit --help` on push to `main` and pull requests. `leverage-platform` is fetched from its public GitHub repo as a regular dependency, so CI imports the same platform code as local dev. No deploy key, no auth wall.

## Package layout (will grow at Gate 2)

```
ai-leverage-audit/
├── src/
│   └── ai_leverage_audit/
│       ├── __init__.py
│       ├── cli.py              # Gate 1 (current)
│       ├── schemas.py          # Gate 2
│       ├── agents.py           # Gate 2
│       ├── prompts.py          # Gate 2
│       ├── eval_config.py      # Gate 2
│       └── workflow.py         # Gate 2
├── fixtures/intakes/           # Gate 2
└── tests/
    ├── test_smoke.py           # Gate 1 (current)
    ├── test_intake_validation.py   # Gate 2
    ├── test_rules.py               # Gate 2
    └── test_workflow_e2e.py        # Gate 2
```

## License / privacy

Private repository. Do not redistribute.

# ai-leverage-audit

> **AI Operating Mentor for solopreneurs and small business owners.** Diagnoses business workflows, identifies where AI creates real leverage, designs a 30-day experiment with success and failure metrics, and produces a first version of a business-specific playbook.

The full product spec lives in the [`leverage-platform`](https://github.com/DEV800-ai/leverage-platform) repo under `docs/product/`:

- [`PRODUCT_VISION.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_VISION.md) — positioning, market pain, MVP wedge.
- [`PRODUCT_MVP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_MVP.md) — V1 spec: intake schema, 7 output artifacts, agent workflow, success criteria, non-goals.
- [`PRODUCT_ROADMAP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_ROADMAP.md) — three gates to V1, evidence-gated V2 bets.

## Status

**Gate 1 — Skeleton runs.** The CLI is wired (`audit --help`), the package imports, CI is green. No Audit logic yet.

Next: **Gate 2** — implement the 7 agents, prompts, and eval config from `PRODUCT_MVP.md` §3–§6. One synthetic intake must produce `EvalReport.accepted=true` against `MockLLMProvider`, and an opt-in live test must do the same against real Anthropic.

## Local development

```bash
# Clone leverage-platform as a sibling directory:
git clone git@github.com:DEV800-ai/leverage-platform.git ../leverage-platform

# Install with the local platform integration:
uv sync --extra dev --extra platform

# Smoke check:
uv run audit --help

# Tests:
uv run pytest
```

The `platform` extra brings in `leverage-platform` from `../leverage-platform/` via `[tool.uv.sources]`. With the extra installed, `test_smoke.py::test_leverage_platform_optional_at_gate_1` actually exercises the platform import. Without it, that test is skipped.

## Gate 1 vs Gate 2 — CI explanation

`leverage-platform` is currently a private repo. The product fork's CI workflow cannot `git clone` it without credentials. Two paths to fix:

1. **Make `leverage-platform` public** — preferred long-term; it's reusable infra with no secrets. Decided at Gate 2 boundary.
2. **Add a deploy key on the platform repo** — works while the platform stays private. Defers the decision.

For **Gate 1**, CI skips the platform dependency entirely:

- ✅ ruff lint
- ✅ pytest (the platform-import test is auto-skipped)
- ✅ uv build
- ✅ `audit --help`

At **Gate 2**, when the first real e2e test exists and the smoke test must actually import platform code, one of paths (1) or (2) above gets resolved.

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

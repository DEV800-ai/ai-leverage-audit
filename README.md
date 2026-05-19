# ai-leverage-audit

> **Diagnose → Test → Evolve.** We help small businesses identify where AI actually helps, test one low-risk workflow over 30 days, and evolve toward the right level of AI adoption over time.

The full product spec lives in the [`leverage-platform`](https://github.com/DEV800-ai/leverage-platform) repo under `docs/product/`:

- [`PRODUCT_VISION.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_VISION.md) — positioning, market pain, MVP wedge.
- [`PRODUCT_MVP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_MVP.md) — V1 spec: intake schema, 7 output artifacts, agent workflow, success criteria, non-goals.
- [`PRODUCT_ROADMAP.md`](https://github.com/DEV800-ai/leverage-platform/blob/main/docs/product/PRODUCT_ROADMAP.md) — three gates to V1, evidence-gated V2 bets.

## Status

**Gate 3 — Structurally accepted on 8 real-shape intakes** (gpt-4o, 8/8 with 16/16 criteria each). Eight sanitized sample fixtures are committed: dental clinic, solo consultant, home cleaning, fitness studio, DTC e-commerce, podcaster, wedding photographer (deliberately messy), and supermarket owner. A self-intake (freelance app developer) was tested and accepted but not committed as a sanitized fixture. See `fixtures/intakes/samples/` and `docs/GATE_3_RESULTS.md` for the evidence. **Live owner reactions are the only remaining gate** — see `docs/LIVE_OWNER_REACTION_PLAYBOOK.md`.

The product follows a three-stage loop — **Diagnose → Test → Evolve** — documented in [`docs/PRODUCT_LIFECYCLE.md`](docs/PRODUCT_LIFECYCLE.md). Stage 3 (Evolve) is designed only in [`docs/CYCLES.md`](docs/CYCLES.md) and will be built after the first owner reaches day 30.

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

### V1 intake flow — operator-assisted

The CLI requires a structured JSON file (`AuditIntake`). It does not yet accept raw owner text directly. The current flow is:

```
owner fills INTAKE_TEMPLATE.md (free text)
  → operator converts to AuditIntake JSON
  → audit run --intake <file>.json
```

A future `audit convert-intake` command will automate the conversion step. It is not implemented yet — build it after the first real owner reactions confirm the intake format is stable.

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

## Package layout

```
ai-leverage-audit/
├── src/ai_leverage_audit/
│   ├── cli.py                  # `audit run` + `audit render` entry points
│   ├── schemas.py              # AuditIntake + 6 output schemas
│   ├── prompts.py              # 6 LLM prompt templates
│   ├── eval_config.py          # AuditState + 10 deterministic rules + 6-question rubric
│   ├── agents.py               # 7 agents (6 LLM + 1 pure Critic)
│   ├── workflow.py             # run_audit orchestration
│   └── render.py               # JSON → friend-shareable markdown
├── fixtures/intakes/
│   ├── INTAKE_TEMPLATE.md      # friend-friendly questionnaire (sections 1-5 + measurement baseline)
│   ├── synthetic_consultant.json   # the canonical Gate-2 mock-provider fixture
│   └── samples/                # 8 curated real-shape profiles for replay
├── fixtures/feedback/
│   └── samples/                # 8 synthetic post-audit feedback responses
├── docs/
│   ├── PRODUCT_LIFECYCLE.md    # three-stage model: Diagnose → Test → Evolve
│   ├── LIVE_OWNER_REACTION_PLAYBOOK.md  # current next step: sending audits to real owners
│   ├── GATE_3_PLAYBOOK.md      # archived Gate 3 structural-testing process
│   ├── GATE_3_RESULTS.md       # evidence table: 8 profiles, model, accept/reject, cost
│   └── CYCLES.md               # Stage 3 (Evolve) technical design — not yet implemented
└── tests/
    ├── test_smoke.py
    ├── test_intake_validation.py
    ├── test_rules.py
    ├── test_render.py
    ├── test_sample_intakes.py  # parametrized — each sample loads as AuditIntake
    └── test_workflow_e2e.py    # mock-provider + opt-in live (RUN_LIVE_TESTS=1)
```

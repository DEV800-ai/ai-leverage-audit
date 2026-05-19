# Gate 3 Playbook — Archived

**Status:** Complete. Structural sample testing finished 2026-05. See [`GATE_3_RESULTS.md`](GATE_3_RESULTS.md) for the evidence table.

Gate 3 structural acceptance required the audit pipeline to produce valid, accepted output across 8 distinct real-shape business profiles. That bar was met: 8/8 profiles accepted, 16/16 eval criteria passed per run, on gpt-4o.

**The remaining validation is live owner reaction, not more structural tests.**

For the current next step — sending audits to real owners and collecting feedback — see [`LIVE_OWNER_REACTION_PLAYBOOK.md`](LIVE_OWNER_REACTION_PLAYBOOK.md).

---

## What "structural acceptance" meant

| Criterion | Bar | Result |
| --- | --- | --- |
| `EvalReport.accepted` | true on first run | 8/8 |
| Deterministic rules passed | all 10 | 16/16 per run (10 rules + 6 rubric) |
| No Pydantic ValidationErrors | 0 | 0 |
| Model | gpt-4o | confirmed |

Structural acceptance does **not** mean the output is useful to a real owner. That is what live owner reactions measure.

## Sample fixtures committed

Eight sanitized profiles in `fixtures/intakes/samples/`:

| File | Business shape |
| --- | --- |
| `dental_clinic.json` | Small services (health) |
| `solo_consultant.json` | Solo consultant / freelancer |
| `home_cleaning.json` | Small services (home) |
| `fitness_studio.json` | Small services (fitness) |
| `ecommerce_brand.json` | DTC e-commerce |
| `podcaster.json` | Creator / media |
| `photographer.json` | Freelancer, deliberately messy intake |
| `supermarket_owner.json` | Product retail, includes measurement baseline |

A self-intake (freelance app developer) was tested and accepted but not committed as a sanitized fixture.

## Intake format used

At the time of Gate 3 testing, `AuditIntake` had no `measurement_context_text` field. The supermarket fixture (added post-Gate 3) is the first to include measurement baseline data. Future live-owner intakes should use the updated `INTAKE_TEMPLATE.md` which includes section 4 (measurement baseline).

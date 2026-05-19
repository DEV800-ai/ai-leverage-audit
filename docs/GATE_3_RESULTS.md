# Gate 3 Results

**Status:** Structurally accepted. Date: 2026-05. Model: gpt-4o.

All 8 profiles passed `EvalReport.accepted=true` on first run, with all 10 deterministic rules and 6 rubric questions met (16/16 criteria each).

## Evidence table

| Profile | Fixture | Model | Accepted | Rules failed | Cost (USD) | Notes | Markdown generated | Owner reaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dental clinic | `dental_clinic.json` | gpt-4o | ✅ | none | ~$0.06 | Appointment + billing workflows | ✅ | not yet |
| Solo consultant | `solo_consultant.json` | gpt-4o | ✅ | none | ~$0.06 | Proposal + CRM workflows | ✅ | not yet |
| Home cleaning | `home_cleaning.json` | gpt-4o | ✅ | none | ~$0.06 | Scheduling + quote workflows | ✅ | not yet |
| Fitness studio | `fitness_studio.json` | gpt-4o | ✅ | none | ~$0.06 | Member comms + class scheduling | ✅ | not yet |
| DTC e-commerce | `ecommerce_brand.json` | gpt-4o | ✅ | none | ~$0.06 | Order + customer support workflows | ✅ | not yet |
| Podcaster | `podcaster.json` | gpt-4o | ✅ | none | ~$0.06 | Production + distribution workflows | ✅ | not yet |
| Freelance app dev (self) | not committed | gpt-4o | ✅ | none | ~$0.06 | Self-intake; sanitized fixture not committed | ✅ | not yet |
| Wedding photographer | `photographer.json` | gpt-4o | ✅ | none | ~$0.06 | Deliberately messy intake; still accepted | ✅ | not yet |

Cost estimates are approximate (~$0.06/run at gpt-4o rates at time of testing). Actual per-run cost is queryable from `audit.db`:

```bash
sqlite3 audit.db "SELECT SUM(cost_usd) FROM agent_run WHERE workflow_run_id = '<uuid>';"
```

## What this confirms

- The pipeline produces structurally valid output across 8 distinct business shapes.
- Deliberately messy intake (photographer) does not break the pipeline.
- gpt-4o is reliable at 8/8. gpt-4o-mini was tested and is not reliable enough for owner-facing runs (~1 in 3 hits a Pydantic error or consistency rule violation).

## What this does not confirm

- That the output is useful to a real owner.
- That the bet feels specific enough to act on.
- That the keep-human list matches what owners actually care about.
- That the 30-day experiment is the right size.

Those questions are answered by live owner reactions. See [`LIVE_OWNER_REACTION_PLAYBOOK.md`](LIVE_OWNER_REACTION_PLAYBOOK.md).

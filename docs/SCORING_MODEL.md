# AI Leverage Prioritization Model — Scoring Model

The leverage analyst ranks workflows using a **Constraint-Aware Multi-Criteria Decision Analysis** model. This document defines the criteria, formula, and hard constraints.

The model is not a pure optimiser. The highest score is not automatically the selected bet. The system selects the best 30-day bet by combining the score with feasibility and constraint checks.

---

## Positive criteria

These increase a workflow's leverage score.

| Criterion | What it measures |
| --- | --- |
| `frequency_score` | How often the workflow runs per week |
| `time_sink_score` | Minutes per week currently lost to it |
| `revenue_impact_score` | Direct effect on revenue when it goes wrong or well |
| `pain_score` | How much friction the owner reports |
| `repeatability_score` | Whether the task is the same each time |
| `data_availability_score` | Whether inputs are structured and accessible |
| `adoption_likelihood_score` | Whether the owner is likely to actually use the tool |

---

## Negative criteria

These reduce a workflow's leverage score.

| Criterion | What it measures |
| --- | --- |
| `error_risk_score` | Consequence severity if AI makes a mistake |
| `customer_sensitivity_score` | Whether errors are visible to customers |
| `setup_complexity_score` | Effort required to set up the experiment |
| `integration_complexity_score` | Number of systems that need to connect |
| `human_judgment_needed_score` | Proportion of steps requiring owner judgment |
| `maintenance_risk_score` | Likelihood of the tool breaking or drifting over time |

---

## Scoring formula

```
Score(workflow) =
  w1 * time_sink_score
+ w2 * frequency_score
+ w3 * revenue_impact_score
+ w4 * pain_score
+ w5 * repeatability_score
+ w6 * data_availability_score
+ w7 * adoption_likelihood_score
- w8 * error_risk_score
- w9 * customer_sensitivity_score
- w10 * setup_complexity_score
- w11 * integration_complexity_score
- w12 * maintenance_risk_score
- w13 * human_judgment_needed_score
```

Weights are currently implicit in the LLM leverage analyst prompt. Explicit numeric weights are a future calibration step once owner feedback data accumulates.

---

## Hard constraints

These are applied after scoring. A workflow that violates a hard constraint is excluded from the bet recommendation regardless of its score.

| Constraint | Source |
| --- | --- |
| `monthly_budget` | Owner-supplied in intake |
| `weekly_setup_hours` | Owner-supplied in intake |
| `things_refused_to_automate` | Owner-supplied in intake |
| `technical_readiness` | Inferred from tools in use |
| `legal / medical / financial sensitivity` | Inferred from business type and error-sensitive areas |
| `customer trust sensitivity` | Inferred from customer-facing workflow flags |

---

## Bet selection rule

The recommended 30-day bet must satisfy all of the following:

```
high leverage score
low enough risk
testable within 30 days
within monthly budget
within weekly setup hours
does not violate keep-human boundaries
does not require building a large system first
targets a single sub-activity (not the whole workflow)
```

The last rule is the MINIMALITY RULE: a bet that targets "automate invoicing" is too broad. A bet that targets "automate product name matching in invoice entry" is testable.

---

## "No AI needed" output

The system must be able to return a recommendation of no bet. This happens when:

- All high-value workflows have high error risk and high human judgment dependency
- The owner's budget or time cannot support any experiment
- The workflow is not mature enough (inconsistent process, no structured inputs)
- The correct recommendation is to fix the process before adding AI

This is not a failure state. It is a valid and honest output.

---

## Sequential learning

After a 30-day bet, the system updates its understanding of the workflow's scores based on observed outcomes. Example:

```
Initial assumption: invoice scanning will reduce manual entry time by 50%.
Observed result:    only 20% reduction — product matching was harder than expected.

Learning:
  Reduce automation readiness score for invoice matching.
  Recommend AI-assisted extraction + human approval, not full automation.
  Do not recommend POS integration yet.
```

This turns the product into a learning system rather than a one-time report generator. The `OutcomeReport` schema captures the evidence; `run_reflection()` uses it to update the leverage ranking in the next cycle.

---

## Relationship to the LLM agents

The current implementation uses LLM agents to score and rank workflows. The agents are instructed to reason across these criteria explicitly — the MCDA structure is embedded in the `LEVERAGE_ANALYST_PROMPT`. Explicit numeric weights are not yet implemented; they are a calibration target for after the first real-owner feedback cycle.

The scoring model documented here is the intended behaviour. If an agent deviates from it, that is a prompt engineering or eval problem.

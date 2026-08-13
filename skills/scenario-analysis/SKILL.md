---
name: scenario-analysis
description: Run and explain deterministic rates and credit shock scenarios with explicit assumptions, provenance, and limitations.
license: MIT
covers:
  - src/agents/multi_agent.py
  - src/analytics/scenario.py
  - contracts/tools/scenario_analysis.schema.json
last_verified_commit: 6c36d81
---

# scenario-analysis

Use this skill when a portfolio question asks what happens under an explicit
market shock or asks to compare two shocks. The Quant specialist owns the
workflow, but the deterministic scenario engine is not implemented until Day
12.

## Workflow

1. Identify the requested shock type, magnitude, horizon, and portfolio.
2. List the market and position inputs needed to calculate the result.
3. Reject ambiguous units, unsupported shock types, or missing portfolio data.
4. Call `scenario_analysis` with explicit positions, shock units, and horizon.
5. Report first-order impact, assumptions, provenance, and the fact that
   convexity, liquidity, and nonlinear repricing are outside this engine.
6. Never convert a scenario result into an order or an unsupported forecast.

## Required output

Return the normalized scenario request, missing inputs, execution status, and
limitations. Never present a model-generated number as a calculated shock
result and never turn the scenario into an unsupported trade recommendation.

---
name: scenario-analysis
description: Frame portfolio shock scenarios, validate required inputs, and report limitations without inventing results; deterministic scenario execution is added on Day 12.
license: MIT
covers:
  - src/agents/multi_agent.py
last_verified_commit: 73a1ed3
---

# scenario-analysis

Use this skill when a portfolio question asks what happens under an explicit
market shock or asks to compare two shocks. The Quant specialist owns the
workflow, but the deterministic scenario engine is not implemented until Day
12.

## Day 5 stub workflow

1. Identify the requested shock type, magnitude, horizon, and portfolio.
2. List the market and position inputs needed to calculate the result.
3. Reject ambiguous units, unsupported shock types, or missing portfolio data.
4. Do not estimate or narrate a numeric impact before a deterministic scenario
   tool returns one.
5. State that scenario execution is unavailable until the Day 12 deterministic
   engine exists. Existing risk metrics may describe historical risk, but they
   are not a substitute for a forward shock.

## Required output

Return the normalized scenario request, missing inputs, execution status, and
limitations. Never present a model-generated number as a calculated shock
result and never turn the scenario into an unsupported trade recommendation.

---
name: portfolio-optimization-narration
description: Explain constrained portfolio optimization outputs in PM language without turning an allocation proposal into an executable trade instruction.
license: MIT
covers:
  - src/analytics/optimizer.py
  - contracts/tools/optimize_portfolio.schema.json
last_verified_commit: 2332962
---

# portfolio-optimization-narration

Use this skill after the deterministic optimizer returns a result.

## Required workflow

1. State the requested method: maximum Sharpe, minimum volatility, or risk parity.
2. Compare current and proposed weights, including per-asset deltas and total turnover.
3. Report expected return, volatility, Sharpe when available, transaction-cost assumption, and binding constraints.
4. Explain that expected returns/covariance, classifications, and holdings may be mock or public inputs.
5. Ask for human approval and data-freshness confirmation before any allocation change.

Never calculate missing metrics in prose, silently relax infeasible constraints,
or generate orders. The optimizer is a decision-support tool, not an execution
system.

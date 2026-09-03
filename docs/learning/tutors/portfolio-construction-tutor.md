# Portfolio construction — deep dive

*Companion to [`.github/agents/portfolio-construction-tutor.agent.md`](../../../.github/agents/portfolio-construction-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py portfolio-construction-tutor --quiz`.*

## What this actually is

Portfolio construction is the discipline of turning a view (expected returns,
risk estimates, constraints) into a set of portfolio weights — and, just as
importantly, into an honest account of what that set of weights assumes,
costs to implement, and might get wrong. It is not the same discipline as
trading: construction produces a *proposal* for a human to review; execution
is a separate, later, and in this repository explicitly out-of-scope step.

Three classical approaches dominate the field, and this repository implements
all three as one function with a `method` switch:

- **Maximum Sharpe** picks the weights that maximize expected return per unit
  of volatility — the textbook "optimal" portfolio on the efficient frontier,
  and also the most sensitive to estimation error in the inputs.
- **Minimum volatility** ignores expected return entirely and picks the
  lowest-risk point on the frontier — more robust to bad return estimates,
  at the cost of potentially leaving return on the table.
- **Risk parity** allocates so that each asset contributes roughly equal risk
  to the portfolio, rather than equal capital — a response to the observation
  that a naive equal-weight portfolio is usually dominated by its riskiest
  asset's risk contribution, not its capital weight.

The recurring theme across all three, and across this whole topic, is that an
optimizer's output is only as trustworthy as its inputs, and a real
institutional process needs to know not just the proposed weights but the
turnover, cost, and constraint feasibility of getting there.

## Core concepts

- **Expected return and covariance.** The two required inputs to every
  classical mean-variance method. This repository treats them as explicit,
  caller-supplied, auditable numbers — never inferred or hidden inside the
  optimizer.
- **The efficient frontier.** The set of portfolios that offer the best
  possible expected return for each level of risk. Max-Sharpe and
  min-volatility are both single points on this frontier.
- **Risk parity / equal risk contribution.** An allocation where each asset's
  marginal contribution to total portfolio variance is equal, computed here
  via hierarchical risk parity (HRP) rather than a naive inverse-variance
  split.
- **Turnover.** How much of the portfolio has to change hands to move from
  the current weights to the proposed ones — computed here as one-way
  turnover, half the sum of absolute weight deltas.
- **Concentration.** The largest single-asset weight in a proposal; an
  institutional constraint, not just a diversification preference.
- **Feasibility.** Whether a proposal satisfies its stated turnover and
  concentration limits. An infeasible proposal is not silently adjusted to
  fit — it fails loudly, so a human decides whether to relax a constraint or
  accept the current allocation.
- **The next institutional layer (not yet built).** Tracking error and
  active risk versus a benchmark, group/factor constraints, downside/CVaR
  risk, shrinkage and Black-Litterman inputs, liquidity/market-impact costs,
  walk-forward out-of-sample validation, and robust/uncertainty-aware
  allocations — all named explicitly in `README.md`'s "Portfolio optimization
  depth" section as roadmap, not implemented.

## How this repository implements it

Everything lives in `src/analytics/optimizer.py`'s `optimize_portfolio()`,
which is long-only (no shorting) and takes an explicit `method` of
`"max_sharpe"`, `"min_volatility"`, or `"risk_parity"`.

**Validation comes first.** `_validate_inputs()` rejects, before any
optimization runs: fewer than two assets; mismatched asset sets across
`expected_returns`, `covariance`, and `current_weights`; weight bounds outside
`[0, 1]` or out of order; `current_weights` that don't sum to 1 or contain a
negative value; and a covariance matrix that isn't symmetric
positive-semidefinite (checked via `np.allclose(matrix, matrix.T)` and
`np.linalg.eigvalsh(matrix) >= -1e-10`). Verified directly:

```python
from src.analytics.optimizer import _validate_inputs
_validate_inputs(
    {"A": 0.1, "B": 0.1},
    {"A": {"A": 1, "B": 0.5}, "B": {"A": 0.9, "B": 1}},  # not symmetric
    {"A": 0.5, "B": 0.5},
    (0.0, 1.0),
)
# ValueError: covariance must be symmetric and positive semidefinite
```

**`max_sharpe` and `min_volatility` go through PyPortfolioOpt's
`EfficientFrontier`** (`frontier.max_sharpe(risk_free_rate=...)` or
`frontier.min_volatility()`), then `frontier.clean_weights()`.

**`risk_parity` goes through `HRPOpt`**, with a load-bearing fallback: current
PyPortfolioOpt releases, on current SciPy, raise an `AttributeError`
referencing a removed private constant `_LINKAGE_METHODS` when `HRPOpt`'s
hierarchical clustering step runs. Rather than let that crash bubble up (or
silently swallow it), `optimize_portfolio()` catches exactly that error,
re-raises anything else, and falls back to a **deterministic inverse-volatility
weighting**: `weights[asset] = 1 / sqrt(variance[asset])`, normalized. This is
disclosed in the function's own comment, and the tutor's job is to teach it as
a *real, documented limitation* — not a hidden bug, and not the "real" HRP
algorithm either; it's a simpler proxy that activates only on this specific
compatibility break.

**Every method's raw weights get clipped to zero and renormalized** (`weights
= {asset: max(0.0, ...) for ...}` then divided by their sum) before turnover
and concentration are checked — a tiny negative weight PyPortfolioOpt
sometimes returns due to floating-point noise doesn't count as a short
position or an infeasibility.

**`compare_to_current()` computes per-asset deltas and one-way turnover:**
`0.5 * sum(abs(delta) for delta in deltas.values())`. Verified:

```python
from src.analytics.optimizer import compare_to_current
compare_to_current({"A": 0.3, "B": 0.7}, {"A": 0.5, "B": 0.5})
# ({'A': -0.2, 'B': 0.19999999999999996}, 0.19999999999999998)
```

**Feasibility is enforced by raising, not clipping:** if the computed turnover
exceeds `max_turnover`, `optimize_portfolio()` raises `ValueError` with the
actual computed figure in the message (`f"optimization exceeds max_turnover:
{turnover:.6f}"`). A `max_concentration` breach also raises, but its message
does *not* include the computed figure (`"optimization exceeds
max_concentration"`, no number) — worth knowing if you're debugging from the
exception text alone. Either way, this is the concrete mechanism behind
"infeasible means a human decides" — there is no silent constraint-relaxation
path in this code.

**Every result carries `"mock": True`** — a literal field in the returned
dict, not just documentation — which the Fundamental/Quant specialist prompts
require surfacing to the caller as a proposal, never an executable order.

## Worked walkthrough

```python
from src.analytics.optimizer import optimize_portfolio

expected_returns = {"A": 0.10, "B": 0.04}
covariance = {"A": {"A": 0.09, "B": 0.0}, "B": {"A": 0.0, "B": 0.01}}
current_weights = {"A": 0.5, "B": 0.5}

optimize_portfolio("max_sharpe", expected_returns, covariance, current_weights)
```

Actual output (run 2026-09-02):

```json
{
  "method": "max_sharpe",
  "weights": {"A": 0.21739, "B": 0.78261},
  "expected_return": 0.05304,
  "volatility": 0.10187,
  "sharpe": 0.52068,
  "turnover": 0.28261,
  "transaction_cost": 0.0,
  "constraints": {"max_turnover": 1.0, "max_concentration": 1.0},
  "mock": true
}
```

Now run the same inputs through `"min_volatility"` and `"risk_parity"` and
compare — the ordering is not what intuition might predict.
`min_volatility` gives A the least weight of the three (`{"A": 0.1, "B":
0.9}`, volatility 0.0949 versus max-Sharpe's 0.1019), which fits the
"minimize variance" objective given A's variance (0.09) is 9x B's (0.01).
`risk_parity`'s inverse-volatility fallback lands at `{"A": 0.25, "B":
0.75}` — a 1:3 weight ratio, from weighting each asset inversely to its own
standard deviation (`1/sqrt(0.09) : 1/sqrt(0.01)` normalized). That 0.25 is
actually *larger* than max-Sharpe's 0.21739, not "between" min-volatility and
max-Sharpe as the numbers might suggest at a glance: risk parity's
inverse-volatility heuristic never looks at expected return at all, only the
volatility ratio, while max-Sharpe's 0.21739 is the result of a genuine
risk/return trade-off that partially — but not fully — offsets A's higher
volatility against its much higher expected return (0.10 vs. B's 0.04). In
this particular example that trade-off happens to land max-Sharpe's weight on
A *below* risk parity's, which is a useful reminder that "which method is
more aggressive toward a given asset" depends on the specific numbers, not on
a general ranking between the three methods.

Then try tightening the constraint until it breaks:

```python
optimize_portfolio(
    "max_sharpe", expected_returns, covariance, current_weights,
    max_turnover=0.01,
)
# ValueError: optimization exceeds max_turnover: 0.282610
```

That's `compare_to_current()`'s actual computed turnover (0.28261) appearing
directly in the exception — not a generic message, the real number.

## Common pitfalls

- **Treating the optimizer's output as an order.** `optimize_portfolio()`
  returns a proposal with `mock: True` and constraint metadata attached, not
  an executable instruction. The correct response to "just place the trades"
  is to redirect to human-reviewed allocation analysis, never to comply.
- **Assuming missing inputs can be filled in.** `_validate_inputs()` exists
  specifically so nobody — human or model — quietly invents an expected
  return or covariance value that wasn't actually supplied. A missing input
  is a reason to ask for it, not to guess a plausible-looking number.
- **Relaxing a constraint to make an infeasible result "pass."** When
  `optimize_portfolio()` raises on a turnover or concentration breach, the
  correct next step is a human decision — accept the current allocation,
  supply a different one, or explicitly widen the limit with a stated reason
  — never silently loosening the constraint until the error goes away.

## Further reading

- [`docs/reference/REFERENCES.md#portfolio-optimization-and-portfolio-construction`](../reference/REFERENCES.md#portfolio-optimization-and-portfolio-construction)
  — the full reading path (PyPortfolioOpt, CVXPY, Cvxportfolio, Riskfolio-Lib,
  skfolio, vectorbt) this repository's implementation is one point within.
- `README.md`'s "Portfolio optimization depth" section for the exact
  implemented-versus-roadmap boundary.
- `tests/unit/analytics/test_optimizer.py` for the full behavioral contract
  in test form, including the turnover/concentration breach cases.

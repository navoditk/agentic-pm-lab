# FICC fundamentals — deep dive

*Companion to [`docs/agent-templates/ficc-tutor-agent.agent.md`](../../agent-templates/ficc-tutor-agent.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py ficc-tutor-agent --quiz`.*

> **Scope note.** This page covers the fixed-income concepts needed to understand this repository's tools — enough to reason about what the agent is calling and whether its answer is sane. It is not a fixed-income curriculum. For the derive-it-yourself treatment — bond pricing, duration, DV01, convexity, key-rate duration, Z-spread, OAS, CDS, and MBS prepayment, each with tested code, a notebook, and a worked example — see [pm-mechanics](https://github.com/navoditk/pm-mechanics), whose fixed-income track runs to 37 reference pages. Every term this page introduces in passing is treated in full there, including the settlement mechanics below (accrued interest, clean versus dirty price, day-count conventions) and the point-in-time and look-ahead discipline, which pm-mechanics covers as [backtesting biases](https://github.com/navoditk/pm-mechanics/blob/main/reference/concepts/backtesting_biases.md).

## What this actually is

FICC stands for fixed income, currencies, and commodities — the trading-desk
umbrella term for everything that isn't equities. This repository's FICC track
narrows that to fixed income: bonds, the interest-rate curves that price them,
and the funding and credit markets around them.

A bond is a promise to pay known cash flows on known dates, and pricing one
means discounting those cash flows on a curve. Everything else — duration,
DV01, spread duration, carry — answers "how does that price move when rates,
spreads, or time move?" What separates the analysis from a spreadsheet guess
is precision about *which* rate, *whose* spread, *what* day-count convention,
and *as of which date*: get one wrong and the number is confidently wrong
rather than obviously broken.

## Core concepts

Orientation only. These are pm-mechanics' subject, where each has a reference
page, tested code, and a notebook that derives it — follow the link rather
than learning it from this page.

- **Yield curve** — yields on similar debt across maturities; nearly every
  other calculation starts by reading a rate off it. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/curve_construction/)
- **Duration** — approximate % price change per 1pp yield move; assumes a
  small *parallel* shift. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/duration/)
- **DV01** — the same sensitivity in dollars, per basis point; what you size
  a hedge with. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/dv01/)
- **Key-rate duration** — duration measured at individual curve points, so
  you can see *where* the risk sits. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/key_rate_duration/)
- **Spread duration** — the credit analogue: sensitivity to the bond's own
  spread, independent of the risk-free curve. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/spread_duration/)
- **Clean / dirty price, accrued interest, day-count** — the quote versus
  what the buyer actually pays, and the convention that decides the
  difference. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/accrued_interest_and_settlement/)
- **Carry and rolldown** — what a position earns from time passing alone, if
  nothing moves. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/carry_and_rolldown/)
- **Point-in-time data / vintage** — a value as it was known on a past date;
  using a later revision in an earlier decision is look-ahead bias.
  [Derive it →](https://navoditk.github.io/pm-mechanics/reference/concepts/backtesting_biases/)

Point-in-time is the one concept above that is also squarely this
repository's own subject: pm-mechanics covers it as backtesting discipline,
while the provenance envelope, vintage-aware connectors, and replay
machinery that enforce it live here.

## How this repository implements it

The bond math lives in `src/analytics/pricers.py`. `price_bond()` takes
explicit cash flows (`time_years`, `amount`), a curve
(`curve_tenors_years`/`curve_rates_pct`), and a `compounding_frequency`, then
discounts each cash flow at the curve rate for its maturity (via
`interpolate_curve()` in `src/analytics/curves.py`) and sums the present
values. `src/analytics/fixed_income.py` builds on that primitive with
`bond_duration_dv01()`, node-level `key_rate_dv01()`, and
`reconcile_bond_price()` for clean price, accrued interest, and dirty price.
These are learning-scale calculations: settlement calendars, day-count
conventions, callable features, and spread curves remain explicit inputs or
deferred production concerns.

Scenario-level risk lives in `src/analytics/scenario.py`. `scenario_analysis()`
takes a list of positions, a `scenario_type` (`"rates"` or `"credit"`), and a
`shock_bps`, and computes each position's impact as
`-weight * sensitivity * shock_bps / 10_000`, where `sensitivity` is read from
the position's `duration` field for a rates shock or `spread_duration` field
for a credit shock. This is a genuine, if first-order (no convexity),
implementation of the duration/spread-duration concepts above — it is real
code, not illustrative planning text, and it is the concrete answer to "how
would this repository actually compute that" for both a rates and a credit
question.

Point-in-time discipline shows up in the ALFRED connector
(`src/education/investment_data_tutor.py`'s `alfred` catalog entry and the
Day 15 provenance envelope): every observation carries both its
`observation_date` and its `vintage`, so a historical decision can be
replayed using only the vintage that would have been available at the time.

## Worked walkthrough

Trace one credit-shock scenario end to end:

1. Read `src/analytics/scenario.py`'s `scenario_analysis()` docstring and
   `ScenarioPosition` TypedDict.
2. Run it directly:
   ```python
   from src.analytics.scenario import scenario_analysis
   scenario_analysis(
       [{"security_id": "A", "weight": 1.0, "spread_duration": 4.0}],
       "credit",
       50,
   )
   ```
3. Confirm the result: `portfolio_return_impact` should be
   `-1.0 * 4.0 * 50 / 10_000 = -0.02` (a 2% loss for a 50bp spread widening on
   a fully-weighted, spread-duration-4 position).
4. Compare that against the `quant-optimize-max-sharpe` and
   `routing-credit-shock-and-concentration` cases in
   `evals/golden_dataset.jsonl` / `evals/routing_cases.jsonl`, which exercise
   the same tool through the agent layer rather than calling it directly.
5. Now try the rates-shock branch with `"duration"` instead of
   `"spread_duration"` and confirm the two fields are genuinely separate
   inputs, not aliases of each other.
6. Run `tests/unit/analytics/test_fixed_income.py` and explain why the
   key-rate result is concentrated at the curve node matching the cash-flow
   maturity.

## Common pitfalls

- **Assuming ticker-level equity data can price a bond.** A ticker and an
  equity closing price carry none of the cash-flow terms, curve, day-count
  convention, or settlement date a bond price actually depends on. The
  correct response to "price this bond from its ticker" is to ask for the
  missing terms or return `needs_review` — not to approximate from
  unrelated data.
- **Using today's data in yesterday's decision.** A current TRACE print or a
  current credit rating did not exist at an earlier historical decision date.
  Feeding it into a backtest at that earlier date is look-ahead bias — the
  fix is always to use the point-in-time/vintage value that was actually
  available then, or to explicitly flag the gap if none exists.
- **Trusting a convenience adapter's number without its provenance.** A
  provider abstraction (like OpenBB) is useful for ergonomics, but the source,
  timestamp, vintage, and any transformation it applied have to travel with
  the number — dropping that metadata turns a traceable figure into an
  unverifiable one, which defeats the entire point of point-in-time
  discipline described above.

## Further reading

- [`docs/reference/REFERENCES.md#ficc--fixed-income-fundamentals`](../../reference/REFERENCES.md#ficc--fixed-income-fundamentals)
  and the adjacent
  [`#fixed-income-data-sources-and-provider-access`](../../reference/REFERENCES.md#fixed-income-data-sources-and-provider-access)
  and
  [`#fixed-income-pm-analytics-reading-checklist`](../../reference/REFERENCES.md#fixed-income-pm-analytics-reading-checklist)
  sections.
- [`docs/learning/ficc-glossary.md`](../ficc-glossary.md) for every term above,
  each with its own public primary source.
- `docs/adr/0018-research-supervisor-pattern.md` and the fixed-income branch
  of `src/capstone/workflow.py` for how curve/spread shocks and bond
  validation fit into the full governed PM workflow.

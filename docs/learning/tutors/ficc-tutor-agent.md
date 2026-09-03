# FICC fundamentals — deep dive

*Companion to [`docs/agent-templates/ficc-tutor-agent.agent.md`](../../agent-templates/ficc-tutor-agent.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py ficc-tutor-agent --quiz`.*

## What this actually is

FICC stands for fixed income, currencies, and commodities — the trading-desk
umbrella term for everything that isn't equities. This repository's FICC track
narrows that scope to fixed income specifically: bonds, the interest-rate
curves that price them, and the funding and credit markets around them.

A bond is, at its core, a promise to pay a series of known cash flows (coupons,
plus principal at maturity) on known dates. Pricing a bond means discounting
those future cash flows back to today using an interest-rate curve. Everything
else in fixed-income analytics — duration, DV01, spread duration, carry,
rolldown — is a way of answering "how does that price change if rates, credit
spreads, or time itself move?" The discipline that separates fixed-income
analysis from a spreadsheet guess is precision about *which* rate, *whose*
credit spread, *what* day-count convention, and *as of which date* — get any
of those wrong and the number is confidently wrong, not just imprecise.

## Core concepts

- **Yield curve.** The set of yields available on similar debt (usually
  Treasuries) at different maturities. Almost every other fixed-income
  calculation starts by reading a rate off this curve at the relevant tenor.
- **Duration.** The approximate percentage price change of a bond for a
  1-percentage-point change in yield. It is the single most-used risk summary
  in fixed income, and also the most commonly overinterpreted — it assumes a
  small, parallel shift in yield, not a large or curve-reshaping one.
- **DV01.** The same idea as duration, but expressed in dollars instead of
  percent, for a one-basis-point (not one-percentage-point) move. Useful for
  directly sizing a hedge across differently-sized positions.
- **Key-rate duration.** Duration measured separately at specific points on
  the curve (2y, 5y, 10y, 30y, ...) instead of assuming the whole curve moves
  together. Shows *where* on the curve a position's risk actually sits.
- **Spread duration.** Duration's analogue for credit risk: price sensitivity
  to the bond's own credit spread widening or narrowing, independent of the
  risk-free curve.
- **Clean price / dirty price / accrued interest.** The quoted ("clean")
  price excludes interest that has built up since the last coupon; the price
  actually paid at settlement ("dirty") adds that accrued interest back in.
- **Day-count convention.** The rule for turning calendar days into a
  year-fraction, used to compute that accrued-interest figure. Different
  conventions give different answers from the same coupon rate and dates —
  this is a frequent source of "why don't our numbers match" errors between
  two systems.
- **Carry and rolldown.** What a bond position earns just from time passing,
  assuming nothing else moves: carry from the coupon net of financing cost,
  rolldown from the bond's yield falling (price rising) as it moves down an
  upward-sloping curve toward maturity.
- **Point-in-time data / vintage.** A data value exactly as it was known and
  published on a specific past date. Using a later, revised vintage inside an
  earlier decision or backtest is look-ahead bias — a subtle, easy-to-miss
  error that overstates how good a strategy would actually have looked at the
  time.

## How this repository implements it

The bond math lives in `src/analytics/pricers.py`. `price_bond()` takes
explicit cash flows (`time_years`, `amount`), a curve
(`curve_tenors_years`/`curve_rates_pct`), and a `compounding_frequency`, then
discounts each cash flow at the curve rate for its maturity (via
`interpolate_curve()` in `src/analytics/curves.py`) and sums the present
values. Read the function before assuming more than that: it currently
returns one present-value `price`, not a separate clean price, dirty price,
and accrued-interest breakdown — that split is a real fixed-income concept
(see Core concepts above) that this project's tooling has not yet built as a
distinct calculation. Say so explicitly rather than implying the split
already exists when a learner asks for it.

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

- [`docs/reference/REFERENCES.md#ficc--fixed-income-fundamentals`](../reference/REFERENCES.md#ficc--fixed-income-fundamentals)
  and the adjacent
  [`#fixed-income-data-sources-and-provider-access`](../reference/REFERENCES.md#fixed-income-data-sources-and-provider-access)
  and
  [`#fixed-income-pm-analytics-reading-checklist`](../reference/REFERENCES.md#fixed-income-pm-analytics-reading-checklist)
  sections.
- [`docs/learning/ficc-glossary.md`](../ficc-glossary.md) for every term above,
  each with its own public primary source.
- `docs/adr/0018-research-supervisor-pattern.md` and the fixed-income branch
  of `src/capstone/workflow.py` for how curve/spread shocks and bond
  validation fit into the full governed PM workflow.

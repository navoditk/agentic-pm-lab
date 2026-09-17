# FICC Glossary

Plain-language terms encountered while building agentic-pm-lab. Entries follow
the `ficc-glossary-maintainer` skill and use only public sources.

Scope is deliberately narrow: terms that show up in *this* repository's tools,
fixtures, and agent output. For a glossary spanning a full PM/FICC curriculum —
and reference pages behind each term — see
[pm-mechanics](https://github.com/navoditk/pm-mechanics) (`reference/glossary.md`).

Scope is deliberately narrow. A term gets a full entry here only when it
carries something specific to *this* repository's tools, fixtures, or agent
output. General PM/FICC vocabulary is pm-mechanics' responsibility, and
appears below as one-line orientation with a link rather than being defined
twice in two places that can drift apart.

## General vocabulary

Enough to keep reading a trace without leaving the page. The derivation,
worked example, and tested code for each live in pm-mechanics.

### Accrued interest

Interest earned by the seller since the last coupon, added to the quoted price at settlement. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/accrued_interest_and_settlement/)

### Clean price and dirty price

The quoted price, versus what a buyer actually pays once accrued interest is added. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/accrued_interest_and_settlement/)

### Day-count convention

The rule converting dates into a year-fraction for accrual. Part of the bond's terms, not a formatting choice. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/accrued_interest_and_settlement/)

### Settlement date

When cash and bond change hands, and the date accrued interest is measured to. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/accrued_interest_and_settlement/)

### Duration

Approximate percentage price change for a one-percentage-point yield move, assuming a parallel shift. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/duration/)

### Spread duration

Sensitivity to the bond's own credit spread, independent of the risk-free curve. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/spread_duration/)

### Yield curve

The yields available on similar debt across maturities; where nearly every other calculation starts. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/curve_construction/)

### Repo (repurchase agreement)

Secured short-term borrowing against collateral — the financing leg of carry. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/repo_and_financing/)

### Spread

Yield pickup over a risk-free benchmark: the compensation demanded for credit risk. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/z_spread/)

### Factor beta

A portfolio's sensitivity to one factor, holding the others fixed. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/concepts/factor_risk/)

### Sharpe ratio

Excess return per unit of total volatility. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/concepts/sharpe_ratio/)

### Maximum drawdown

The largest peak-to-trough fall over the measured period. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/concepts/drawdown/)

### Point-in-time data and vintage

A value exactly as it stood on a past date. Using a later revision in an earlier decision is look-ahead bias. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/concepts/backtesting_biases/)

### SOFR (Secured Overnight Financing Rate)

The overnight secured USD benchmark that replaced USD LIBOR. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/fixed_income/repo_and_financing/)

## Terms with repository-specific meaning

Each of these says something about this repository's code or fixtures that a
general definition would not.

## Basis point

**Plain-language definition:** A basis point (bps) is one one-hundredth of a
percentage point (0.01%). It is the standard unit for quoting small rate,
spread, or yield changes in fixed income -- this project's scenario tool takes
its shock size as `shock_bps`.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [Investor.gov: Basis Point](https://www.investor.gov/introduction-investing/investing-basics/glossary/basis-point)

## Callable bond

**Plain-language definition:** A callable bond gives the issuer the right, but
not the obligation, to redeem it before its stated maturity, usually at a
preset call price. That optionality means a callable bond's price and duration
behave differently near a call date than a plain (bullet) bond's. This
project's bond instrument-master validator (`src/ingestion/fixed_income.py`'s
`validate_bond_instrument()`) does not yet check callability at all --
`REQUIRED_BOND_FIELDS` has no `callable`, `call_date`, or `call_price` field,
so a callable bond with an unresolved call provision currently validates the
same as a plain bullet bond if its other required fields are present. That is
a real gap, not a handled case -- say so rather than implying the validator
already protects against it.

**Introduced:** Day 15

**Public source:** [Investor.gov: Callable Bonds (or Redeemable Bonds)](https://www.investor.gov/introduction-investing/investing-basics/glossary/callable-bonds-or-redeemable-bonds)

## Carry and rolldown

**Plain-language definition:** Carry is the return earned just from holding a
bond to the next period -- roughly its coupon minus financing cost. Rolldown
is the additional price gain expected as a bond moves ("rolls down") an
upward-sloping yield curve toward a lower yield as it approaches maturity,
assuming the curve's shape does not change. Together they describe the return
a bond position earns if nothing moves except the passage of time.

**Introduced:** Day 12 (named in `README.md`'s portfolio-optimization roadmap
alongside the Day 12 scenario engine; not yet a separate deterministic tool)

**Public source:** [Corporate Finance Institute: Rolling Down the Yield Curve](https://corporatefinanceinstitute.com/learn/resources/fixed-income/rolling-down-the-yield-curve)

## DV01 (dollar value of a basis point)

**Plain-language definition:** DV01 is the estimated dollar change in a bond
or portfolio's price for a one-basis-point move in yield. Unlike duration,
which is a percentage sensitivity, DV01 is expressed in dollars, which makes
it directly usable for sizing a position-level hedge -- for example, matching
one position's DV01 against an offsetting position's DV01 rather than trying
to compare two differently-sized positions' percentage durations.

**Introduced:** Day 12 (named in `README.md`'s fixed-income analytics roadmap;
the current `src/analytics/scenario.py` engine estimates portfolio impact from
a shock directly rather than reporting a standalone DV01 figure yet)

**Public source:** [WallStreetMojo: DV01](https://www.wallstreetmojo.com/dv01/)

## Key-rate duration

**Plain-language definition:** Key-rate duration measures a bond or
portfolio's price sensitivity to a shift at one specific point on the yield
curve (say, the 5-year point) while holding the rest of the curve fixed,
rather than assuming the whole curve moves in parallel the way ordinary
duration does. Reporting key-rate durations at several maturities (2y, 5y,
10y, 30y, ...) shows *which* part of the curve a position is exposed to, which
a single overall duration number cannot.

**Introduced:** Day 12 (named in `README.md`'s fixed-income analytics roadmap
as the next layer beyond the current parallel-shock `scenario_analysis` tool)

**Public source:** [Corporate Finance Institute: Key Rate Duration](https://corporatefinanceinstitute.com/resources/fixed-income/key-rate-duration)

## N-PORT (SEC Form N-PORT)

**Plain-language definition:** Form N-PORT is a monthly, structured-data
filing that most SEC-registered funds (mutual funds, ETFs, closed-end funds)
must submit disclosing portfolio holdings. It is useful for studying reported
fund exposures, concentration, and holdings changes, subject to a real
reporting lag and possible amendments -- this project's sample pack treats it
as a mock fixture rather than a live connector.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [SEC.gov: Form N-PORT Reporting](https://www.sec.gov/investment/new-form-n-port)

## TRACE (Trade Reporting and Compliance Engine)

**Plain-language definition:** TRACE is FINRA's system for mandatory
reporting of over-the-counter transactions in eligible fixed-income
securities, publishing execution time, price, yield, and (capped) volume. It
is the primary public window into bond-market liquidity, but it is not a
complete, executable order book -- this project's sample pack labels it a
mock fixture pending a licensing decision.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [FINRA: What Is TRACE and How Can It Help Me?](https://www.finra.org/investors/insights/what-is-TRACE)

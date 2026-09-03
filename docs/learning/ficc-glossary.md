# FICC Glossary

Plain-language terms encountered while building agentic-pm-lab. Entries follow
the `ficc-glossary-maintainer` skill and use only public sources.

## Accrued interest

**Plain-language definition:** Accrued interest is interest that has
accumulated on a bond since its last coupon payment but has not yet been paid
to the holder. It is what separates a bond's quoted "clean" price from the
"dirty" price a buyer actually pays at settlement (see *Clean price and dirty
price*).

**Introduced:** Day 20

**Public source:** [Investor.gov: Accrued Interest](https://www.investor.gov/introduction-investing/investing-basics/glossary/accrued-interest)

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

## Clean price and dirty price

**Plain-language definition:** The clean price is a bond's quoted price
excluding accrued interest. The dirty price (also called the "full" or
"invoice" price) is what a buyer actually pays at settlement: clean price plus
accrued interest. Quoting conventions almost always show the clean price, so
accrued interest has to be added back explicitly before a cash settlement
amount is correct.

**Introduced:** Day 20

**Public source:** [Wikipedia: Clean price](https://en.wikipedia.org/wiki/Clean_price)

## Day-count convention

**Plain-language definition:** A day-count convention (for example
Actual/365 or 30/360) is the rule used to convert the calendar time between
two dates into a fraction of a year for computing accrued interest and coupon
amounts. The same nominal coupon rate produces different accrued-interest
figures under different conventions, so a bond's day-count convention must
always be stated explicitly rather than assumed.

**Introduced:** Day 15

**Public source:** [Wikipedia: Day count convention](https://en.wikipedia.org/wiki/Day_count_convention)

## Duration

**Plain-language definition:** Duration measures how sensitive a bond's price is
to a change in interest rates. Modified duration is commonly read as the
approximate percentage price change for a one-percentage-point change in yield,
with price generally moving in the opposite direction from yield.

**Introduced:** Day 2

**Public source:** [FINRA: Duration - What an Interest Rate Hike Could Do to Your Bond Portfolio](https://www.finra.org/investors/insights/duration-what-interest-rate-hike-could-do-your-bond-portfolio)

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

## Factor beta

**Plain-language definition:** A factor beta estimates how much a portfolio's
returns tend to move when a chosen market factor moves by one unit, after
accounting for the other factors in the regression. A beta of 2 to an equity
proxy means the fitted portfolio move is twice the proxy's move, not that every
future observation will follow that relationship.

**Introduced:** Day 3

**Public source:** [Investor.gov: Beta](https://www.investor.gov/introduction-investing/investing-basics/glossary/beta)

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

## Maximum drawdown

**Plain-language definition:** Maximum drawdown is the largest percentage fall
from a portfolio's previous peak to a later trough during the measured period.
It describes the worst observed loss path, not the probability of a future
loss.

**Introduced:** Day 3

**Public source:** [Investopedia: Maximum Drawdown](https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp)

## N-PORT (SEC Form N-PORT)

**Plain-language definition:** Form N-PORT is a monthly, structured-data
filing that most SEC-registered funds (mutual funds, ETFs, closed-end funds)
must submit disclosing portfolio holdings. It is useful for studying reported
fund exposures, concentration, and holdings changes, subject to a real
reporting lag and possible amendments -- this project's sample pack treats it
as a mock fixture rather than a live connector.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [SEC.gov: Form N-PORT Reporting](https://www.sec.gov/investment/new-form-n-port)

## Point-in-time data and vintage

**Plain-language definition:** Point-in-time data preserves the value of an
observation exactly as it was known and published on a specific past date,
distinct from a later-revised value of that same observation. A "vintage" is
one such dated snapshot of a series. Using a later vintage in an earlier
historical decision or backtest silently introduces look-ahead bias -- the
project's ALFRED connector exists specifically to avoid this.

**Introduced:** Day 15

**Public source:** [FRED: API Real-Time Periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)

## Repo (repurchase agreement)

**Plain-language definition:** A repo is a short-term, typically overnight
loan collateralized by securities (often Treasuries): one party sells a
security and agrees to repurchase it the next day at a slightly higher price,
with the price difference acting as interest. Repo rates are a core
funding-market signal, and SOFR is derived from tri-party and bilateral
Treasury repo transactions.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [New York Fed: Secured Overnight Financing Rate Data](https://www.newyorkfed.org/markets/reference-rates/sofr)

## Settlement date

**Plain-language definition:** The settlement date is when a securities
transaction is actually completed and ownership and cash change hands, as
distinct from the trade date, when the transaction was agreed. Most U.S.
securities have settled T+1 (one business day after the trade date) since May
2024, down from the prior T+2 standard.

**Introduced:** Day 15

**Public source:** [Investor.gov: New "T+1" Settlement Cycle -- What Investors Need to Know](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin)

## Sharpe ratio

**Plain-language definition:** The Sharpe ratio compares return above a
risk-free rate with the volatility taken to earn it. A larger value indicates
more excess return per unit of measured volatility, but it does not capture
every kind of risk.

**Introduced:** Day 3

**Public source:** [Investopedia: Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)

## SOFR (Secured Overnight Financing Rate)

**Plain-language definition:** SOFR is a broad measure of the cost of
borrowing cash overnight collateralized by Treasury securities, published
daily by the New York Fed as a volume-weighted median of repo transactions. It
succeeded LIBOR as the primary U.S. dollar reference rate and is a key input
for assessing overnight funding conditions.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [New York Fed: Secured Overnight Financing Rate Data](https://www.newyorkfed.org/markets/reference-rates/sofr)

## Spread

**Plain-language definition:** A spread is the difference between two yields,
usually quoted in basis points. For example, a corporate bond's spread over a
Treasury yield helps separate compensation for credit and liquidity risk from
the underlying government interest rate.

**Introduced:** Day 2

**Public source:** [Federal Reserve Bank of St. Louis: ICE BofA Corporate Bond Index Option-Adjusted Spread](https://fred.stlouisfed.org/series/BAMLC0A0CM)

## Spread duration

**Plain-language definition:** Spread duration measures a bond's price
sensitivity to a change in its own credit spread, as opposed to the
underlying risk-free rate -- expressed the same way ordinary duration is: a
spread duration of 3 implies roughly a 3% price move for a 100bp change in
spread. Lower-rated, fixed-coupon bonds tend to have higher spread duration
than higher-rated or floating-rate ones. This project's `scenario_analysis`
tool takes `spread_duration` as an explicit, caller-supplied position field
for its credit-shock calculation.

**Introduced:** Day 12

**Public source:** [Finance Strategists: Spread Duration](https://www.financestrategists.com/wealth-management/bonds/spread-duration/)

## TRACE (Trade Reporting and Compliance Engine)

**Plain-language definition:** TRACE is FINRA's system for mandatory
reporting of over-the-counter transactions in eligible fixed-income
securities, publishing execution time, price, yield, and (capped) volume. It
is the primary public window into bond-market liquidity, but it is not a
complete, executable order book -- this project's sample pack labels it a
mock fixture pending a licensing decision.

**Introduced:** post-Day-20 public-data expansion

**Public source:** [FINRA: What Is TRACE and How Can It Help Me?](https://www.finra.org/investors/insights/what-is-TRACE)

## Yield curve

**Plain-language definition:** A yield curve compares the yields available on
similar debt at different times to maturity. This project builds a Treasury
curve from FRED observations ranging from one month to thirty years.

**Introduced:** Day 2

**Public source:** [U.S. Department of the Treasury: Interest Rate Statistics](https://home.treasury.gov/resource-center/data-chart-center/interest-rates)

# Data Layer

Day 2 replaces mock market and curve data with public yfinance and FRED data.
Generated databases and API caches live under `data/cache/` and are gitignored.
The security master and portfolio positions remain invented learning fixtures.

## Structured versus unstructured inputs

The PM platform has two intentionally separate ingestion paths:

- **Structured:** prices, macro series, curves, factors, holdings, issuer facts,
  and transaction aggregates. These may feed deterministic analytics only after
  schema, identifier, unit, timestamp, vintage, and quality validation.
- **Unstructured/semi-structured:** filing text, permitted news or event metadata,
  research narratives, thematic evidence, credit commentary, and uploaded PDFs.
  These are retrieved as evidence objects for explanation and challenge; they
  cannot directly change portfolio weights, risk numbers, or execution state.

The optional BigData.com adapter belongs to the second path. Normalize its outputs
into an evidence envelope containing provider, query, entity identifier, source
URL or permitted excerpt, publication date, retrieval time, novelty status,
confidence, and licensing/retention status. Reconcile material claims against
official filings, public macro data, or other approved sources before using them
in a committee artifact.

## Fixed-income data spine

The fixed-income path is intentionally layered rather than represented by one
generic market-data API:

| Domain | Learning/public source | Production lesson |
|---|---|---|
| Treasury curves and rates | U.S. Treasury daily rates, FRED/ALFRED, Federal Reserve fitted curves | Curve methodology, vintages, interpolation, zero/par/forward distinctions |
| Treasury issuance | Treasury Fiscal Data auctions and securities datasets | Supply, auction demand, issue/maturity metadata, and security identifiers |
| Funding | NY Fed SOFR and related reference rates | Collateral, discounting, publication timing, and rate fallbacks |
| Bond liquidity | FINRA fixed-income aggregates and TRACE reports | Sparse OTC observations, capped volume, reporting delays, and licensing |
| Fund holdings | SEC N-PORT and EDGAR | As-filed holdings, reporting lag, amendments, and point-in-time exposure |
| Futures positioning | CFTC Trader-in-Financial-Futures/COT | Rates positioning and release-date versus observation-date semantics |
| Provider abstraction | OpenBB connectors, with direct-source reconciliation | Convenience is not provenance; retain the underlying provider and raw response metadata |

### Bond instrument-master minimum

Before using bond observations in deterministic analytics, the learning schema
should represent `cusip_or_isin`, issuer, coupon, frequency, issue date,
maturity date, call/put/sink features, day-count convention, settlement lag,
calendar, currency, seniority, rating, sector, benchmark/curve mapping, clean
price, dirty price, accrued interest, yield, spread, duration, and convexity.
Missing terms must produce `needs_review` rather than silently defaulting to an
equity-style price or return calculation.

OpenBB can make provider exploration easier, but it does not remove the need for
source-specific terms, security-master resolution, quality checks, or licensed
institutional data. QuantLib and rateslib should be evaluated as deterministic
pricing/curve references; they are not substitutes for market data.

## Ingestion

Set `FRED_API_KEY` in the environment or in the gitignored repo-root `.env`,
then run:

```bash
uv run python -m src.ingestion.load_mock_structured_data
uv run python -m src.ingestion.prices
uv run python -m src.ingestion.macro
```

Both public ingestors normalize source responses before writing DuckDB. Their
JSON caches have a 24-hour TTL by default; a fresh cache avoids another API
request, while an expired cache is replaced atomically.

## Data-card template for future connectors

Before adding a source such as ALFRED, SEC EDGAR, N-PORT, FINRA TRACE,
Kenneth French, GDELT, or an external financial-intelligence provider such as
BigData.com, document:

| Field | Record |
|---|---|
| Owner and source | Publishing organization, endpoint, and source URL |
| Terms | License, attribution, rate limits, retention, and redistribution rights |
| Time semantics | Observation timestamp, publication/filing timestamp, timezone, and revision/vintage behavior |
| Coverage | Instruments, geography, frequency, start date, missing periods, and update cadence |
| Identifiers | Mapping keys, corporate actions, issuer/security resolution, and known collisions |
| Schema | Raw fields, normalized fields, units, currency, and transformations |
| Quality | Freshness, completeness, duplicate, outlier, reconciliation, and drift checks |
| Failure behavior | Timeout, retry, stale-cache, partial-response, and dead-letter policy |
| Reproducibility | Snapshot/version/hash needed to reproduce a research or agent answer |

### Optional external financial-intelligence provider card

BigData.com is a learning and integration reference for narrative mining,
thematic screening, credit-rating monitoring, sentiment/attention signals,
central-bank and inflation-driver digests, and large-scale portfolio briefs. Its
outputs are research evidence, not authoritative market prices or deterministic
risk calculations. The adapter must be feature-flagged, mockable in unit tests,
and able to degrade to `unavailable` or `needs_review` when credentials,
licensing, rate limits, entity resolution, or freshness checks fail.

Before live use, complete the source card for the selected API/product, including
terms and redistribution rights, authentication, coverage, entity resolution,
source timestamps, retention, and whether generated text may be stored or shown.

The most important field for backtesting is what was knowable at the decision
time. A current revised value is not automatically valid historical input.

## DuckDB schema

The default database is `data/cache/portfolio.duckdb`.

| Table | Source | Columns |
|---|---|---|
| `prices` | yfinance: SPY, AGG, TLT, LQD, HYG, GLD | `symbol`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `macro_series` | FRED: Treasury yields, effective Fed Funds, CPI | `series_id`, `date`, `value` |
| `curve_points` | Latest complete date across eight FRED Treasury tenors | `curve_date`, `tenor`, `tenor_years`, `rate_pct`, `series_id` |
| `security_master` | Mock CSV | `security_id`, `name`, `asset_class`, `sector`, `currency`, `issuer` |
| `portfolio_positions` | Mock CSV | `portfolio_id`, `security_id`, `quantity`, `market_value`, `as_of_date` |

`/tools/curve` reads `curve_points` and returns the latest curve unless the
caller supplies a specific `curve_date`.

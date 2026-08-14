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

## Public connectors and the complete source catalog

The post-Day-20 public-data expansion adds tested, provider-neutral retrieval
and normalization paths for the next six sources. These connectors are safe to
exercise with recorded payloads in unit tests; a connector being implemented is
not the same as a live response being captured in an experiment.

| Category | Source | Module/function | Status | Main decision use | Browse sample |
|---|---|---|---|---|---|
| Structured fundamentals/filings | SEC Company Facts/submissions | `src/ingestion/public_investment.py` | Real-capable public connector; `SEC_USER_AGENT` required | As-filed issuer fundamentals and filing evidence | [`sec_companyfacts.json`](samples/public_investment/sec_companyfacts.json) |
| Structured macro vintages | ALFRED | `src/ingestion/public_investment.py` | Real-capable; `FRED_API_KEY` required | Revision-safe macro and curve backtests | [`alfred_vintages.json`](samples/public_investment/alfred_vintages.json) |
| Structured issuance | Treasury auctions | `src/ingestion/public_investment.py` | Real-capable bounded Fiscal Data API path | Issuance and auction-demand context | [`treasury_auctions.json`](samples/public_investment/treasury_auctions.json) |
| Structured funding rates | NY Fed SOFR | `src/ingestion/public_investment.py` | Real-capable daily public path | Funding and repo conditions | [`sofr.json`](samples/public_investment/sofr.json) |
| Structured positioning | CFTC COT | `src/ingestion/public_investment.py` | Real-capable public-reporting path | Weekly futures positioning context | [`cftc_cot.json`](samples/public_investment/cftc_cot.json) |
| Structured factor returns | Kenneth French factors | `src/ingestion/public_investment.py` | Real-capable public archive path | Factor exposure and attribution inputs | [`kenneth_french_factors.csv`](samples/public_investment/kenneth_french_factors.csv) |

The tutor catalog also includes the existing price/macro paths and every
documented deferred source as a small mock fixture. This makes the data shape
and intended use inspectable before terms, licensing, identifiers, and live
quality controls are resolved.

| Category | Source | Current status | Main decision use | Browse sample | Primer |
|---|---|---|---|---|---|
| Structured market | yfinance prices | Real integration; cached public retrieval | Returns, drawdowns, and portfolio analytics | [`yfinance_prices.json`](samples/public_investment/yfinance_prices.json) | [Public-data primer](../docs/REFERENCES.md#public-data-terminology-and-decision-use-primers) |
| Structured macro | FRED | Real integration; key required | Macro regime and scenario inputs | [`fred_macro.json`](samples/public_investment/fred_macro.json) | [Public-data primer](../docs/REFERENCES.md#public-data-terminology-and-decision-use-primers) |
| Structured reference | Security master | Mock fixture | Identifier and issuer resolution | [`security_master.csv`](mock_structured/security_master.csv) | [Data layer](../docs/REFERENCES.md#data-layer-and-provenance) |
| Structured holdings | Portfolio positions | Mock fixture | Read-only portfolio joins | [`portfolio_positions.csv`](mock_structured/portfolio_positions.csv) | [Portfolio data](../docs/REFERENCES.md#backtesting-and-portfolio-construction-realism) |
| Structured holdings | SEC N-PORT | Mock fixture; live connector not integrated | Fund exposure and concentration | [`sec_nport.json`](samples/public_investment/sec_nport.json) | [SEC/N-PORT](../docs/REFERENCES.md#fixed-income-data-sources-and-provider-access) |
| Structured liquidity | FINRA TRACE | Mock fixture; licensing unresolved | OTC bond liquidity context | [`finra_trace.json`](samples/public_investment/finra_trace.json) | [TRACE](../docs/REFERENCES.md#fixed-income-data-sources-and-provider-access) |
| Structured credit | Ratings events | Mock fixture; licensed feed not integrated | Dated credit-review queue | [`ratings_events.json`](samples/public_investment/ratings_events.json) | [Credit data](../docs/REFERENCES.md#fixed-income-data-sources-and-provider-access) |
| Semi-structured events | GDELT | Mock fixture; live ingestion not integrated | Thematic evidence for reconciliation | [`gdelt_events.json`](samples/public_investment/gdelt_events.json) | [News and events](../docs/REFERENCES.md#news-sentiment-and-research-retrieval) |
| Unstructured research | Provider research evidence | Mock fixture; provider decision pending | Traceable narrative evidence | [`bigdata_research.json`](samples/public_investment/bigdata_research.json) | [Narrative evidence](../docs/REFERENCES.md#news-sentiment-and-research-retrieval) |
| Provider adapter | OpenBB | Reference-only adapter | Compare convenience with provenance | [`openbb_provider.json`](samples/public_investment/openbb_provider.json) | [Provider abstraction](../docs/REFERENCES.md#openbb-provider-abstraction) |
| Unstructured documents | PDF/document evidence | Mock fixture; extraction pipeline not integrated | Page-cited research evidence | [`document_pdf.json`](samples/public_investment/document_pdf.json) | [Document evidence](../docs/REFERENCES.md#document-ingestion-and-document-to-skill-design) |

### Browsable sample dataset

The complete representative sample pack is indexed in
[`data/samples/public_investment/README.md`](samples/public_investment/README.md).
Each file is intentionally small and uses either the normalized field shape
expected from a connector or the evidence envelope proposed for a deferred
source. It is invented educational data, not a live snapshot.

Use the samples to answer four questions before connecting a provider:

1. **What does one row represent?** For example, an SEC fact is a concept/unit
   observation, while an ALFRED row is an observation plus a release vintage.
2. **Which fields make it usable?** Look at identifiers, units, observation dates,
   release dates, filing dates, and source URLs.
3. **What investment question can it support?** The samples show whether a
   source is useful for fundamentals, macro regime, issuance, funding,
   positioning, or factor attribution.
4. **What can it not prove?** None of the samples alone establishes causality,
   an allocation, a trade, or investment advice.

Inspect the catalog and sample records without credentials:

```bash
uv run python scripts/investment_data_tutor.py
uv run python scripts/investment_data_tutor.py alfred
uv run python scripts/investment_data_tutor.py alfred --browse
uv run python scripts/investment_data_tutor.py sec-companyfacts --browse
```

Use `.github/agents/investment-data-tutor.agent.md` for a guided explanation of
each source, terminology, provenance, limitations, and how the data can inform
an investment decision. The tutor is read-only and does not provide investment
advice.

The current slice normalizes provider responses but does not silently promote
them into the canonical DuckDB portfolio tables. Live captures should be run as
dated experiments with source terms, raw-response hashes, point-in-time fields,
and findings recorded under `experiments/`. The next implementation step is to
add source-specific DuckDB tables and scheduled/cache policies after a live
response has been reviewed.

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

For future sources such as SEC N-PORT, FINRA TRACE, GDELT, or an external
financial-intelligence provider such as BigData.com—and before promoting any
connector into canonical tables—document:

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

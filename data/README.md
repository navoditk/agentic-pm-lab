# Data Layer

Day 2 replaces mock market and curve data with public yfinance and FRED data.
Generated databases and API caches live under `data/cache/` and are gitignored.
The security master and portfolio positions remain invented learning fixtures.

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

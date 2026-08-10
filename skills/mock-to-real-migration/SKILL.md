---
name: mock-to-real-migration
description: Replace an existing mock implementation with a real one without breaking its interface, contracts, callers, tests, progress tracking, or documentation.
license: MIT
covers:
  - src/api/main.py
  - src/ingestion/cache.py
  - src/ingestion/load_mock_structured_data.py
  - src/ingestion/macro.py
  - src/ingestion/prices.py
last_verified_commit: c39b1f6
---

# mock-to-real-migration

Use this checklist when replacing an existing `# MOCK` implementation. It is
not the workflow for introducing a new tool that has no callers or interface.

## Migration checklist

1. Confirm that the marker's target day has arrived and identify the existing
   interface, response shape, callers, contracts, and covered skills.
2. Implement the real provider behind the same interface. Keep source-specific
   parsing separate from persistence and inject or patch the provider in tests.
3. Add bounded on-disk caching before exercising a public API repeatedly. Keep
   credentials in the environment or a gitignored `.env`, never in code, cache
   files, fixtures, logs, or commits.
4. Replace only the mock data owned by the migration. Preserve explicitly
   deferred mock dependencies and their markers.
5. Repoint callers to the real implementation, then remove the migrated
   `# MOCK` marker. Do not remove a marker merely to change progress status.
6. Add deterministic tests for normalization, persistence, failure behavior,
   and cache freshness. Unit tests must not use a live network.
7. Check every dependent API, MCP capability, canvas capability, contract, and
   skill. Version a contract when its observable shape intentionally changes.
8. Update `ARCHITECTURE.md`, data-schema documentation, and progress checks when
   the source or data flow changes.

## Day 2 example

- `prices` moved from no real source to normalized yfinance ETF observations.
- `macro_series` and `curve_points` now come from FRED; the existing
  `/tools/curve` route reads those points without changing its route.
- `security_master` and `portfolio_positions` remain clearly mocked.
- `data/cache/` supplies the DuckDB database and TTL-governed JSON caches and
  remains gitignored.

The progress tracker scans `src/ingestion/**/*.py`. Removing the stale
price/curve marker while retaining the security-master marker makes the Data
Layer partial, accurately reflecting the mixed real/mock state.

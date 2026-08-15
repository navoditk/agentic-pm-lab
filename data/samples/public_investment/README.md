# Public investment-data sample pack

These files are small, invented, representative samples of normalized records
and deferred-source evidence envelopes. They are not copied provider
responses, do not represent current market values, and must not be used as
investment advice or as evidence of a live provider connection.

| Source | Sample file | What to inspect | Example decision use |
|---|---|---|---|
| SEC Company Facts/submissions | [`sec_companyfacts.json`](sec_companyfacts.json) | CIK, XBRL concept, unit, value, filing date, accession number | Compare fundamentals using only facts filed by the decision date |
| ALFRED | [`alfred_vintages.json`](alfred_vintages.json) | Same observation with two release/vintage dates | Prevent revised macro data from leaking into a historical backtest |
| Treasury auctions | [`treasury_auctions.json`](treasury_auctions.json) | CUSIP, security type/term, auction/issue/maturity dates, bid-to-cover | Add supply and auction-demand context to a duration review |
| NY Fed SOFR | [`sofr.json`](sofr.json) | Effective date, rate, unit, provider fields | Assess overnight repo/funding conditions |
| CFTC COT | [`cftc_cot.json`](cftc_cot.json) | Report date, market, open interest, trader categories | Add weekly positioning context to a rates hedge discussion |
| Kenneth French factors | [`kenneth_french_factors.csv`](kenneth_french_factors.csv) | Monthly factor names, returns, and risk-free rate | Estimate factor exposures and attribution inputs |
| yfinance prices | [`yfinance_prices.json`](yfinance_prices.json) | OHLCV, adjusted close, symbol, and date | Return, drawdown, and portfolio analytics inputs |
| FRED macro | [`fred_macro.json`](fred_macro.json) | Series ID, observation/release dates, value, and unit | Macro regime and scenario inputs |
| SEC N-PORT | [`sec_nport.json`](sec_nport.json) | Fund, filing, CUSIP, holding, and reported value | Holdings exposure and concentration review |
| FINRA TRACE | [`finra_trace.json`](finra_trace.json) | Bond trades, volume, count, caps, and reporting delay | OTC liquidity context, subject to terms |
| Ratings events | [`ratings_events.json`](ratings_events.json) | Agency action, rating, outlook, and publication dates | Dated credit-review queue |
| GDELT events | [`gdelt_events.json`](gdelt_events.json) | Event actors, themes, tone, confidence, and URL | Thematic evidence for reconciliation |
| Provider research evidence | [`bigdata_research.json`](bigdata_research.json) | Evidence envelope, excerpt, novelty, confidence, licensing | Traceable narrative research workflow |
| OpenBB provider metadata | [`openbb_provider.json`](openbb_provider.json) | Adapter, raw/normalized fields, source, and fallback | Compare provider ergonomics without losing provenance |
| Document/PDF evidence | [`document_pdf.json`](document_pdf.json) | Page, section, excerpt, extraction, and trust fields | Page-cited document research |
| Security master | [`../../mock_structured/security_master.csv`](../../mock_structured/security_master.csv) | Identifier, issuer, asset class, sector, and currency | Resolve holdings before analytics |
| Portfolio positions | [`../../mock_structured/portfolio_positions.csv`](../../mock_structured/portfolio_positions.csv) | Portfolio, security, quantity, value, and as-of date | Join holdings to market and evidence data |

Browse these files directly in the repository, or use the read-only tutor:

```bash
uv run python scripts/investment_data_tutor.py
uv run python scripts/investment_data_tutor.py sec-companyfacts
uv run python scripts/investment_data_tutor.py kenneth-french
```

The tutor returns the sample path, a compact sample record, field terminology,
business use, limitations, and the source's current integration status. The
primer mapping for each source is maintained in
[`docs/reference/REFERENCES.md`](../../../docs/reference/REFERENCES.md).

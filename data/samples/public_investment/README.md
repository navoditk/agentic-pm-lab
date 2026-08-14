# Public investment-data sample pack

These files are small, invented, representative samples of the normalized
records produced by `src/ingestion/public_investment.py`. They are not copied
provider responses, do not represent current market values, and must not be
used as investment advice or as evidence of a live provider connection.

| Source | Sample file | What to inspect | Example decision use |
|---|---|---|---|
| SEC Company Facts/submissions | [`sec_companyfacts.json`](sec_companyfacts.json) | CIK, XBRL concept, unit, value, filing date, accession number | Compare fundamentals using only facts filed by the decision date |
| ALFRED | [`alfred_vintages.json`](alfred_vintages.json) | Same observation with two release/vintage dates | Prevent revised macro data from leaking into a historical backtest |
| Treasury auctions | [`treasury_auctions.json`](treasury_auctions.json) | CUSIP, security type/term, auction/issue/maturity dates, bid-to-cover | Add supply and auction-demand context to a duration review |
| NY Fed SOFR | [`sofr.json`](sofr.json) | Effective date, rate, unit, provider fields | Assess overnight repo/funding conditions |
| CFTC COT | [`cftc_cot.json`](cftc_cot.json) | Report date, market, open interest, trader categories | Add weekly positioning context to a rates hedge discussion |
| Kenneth French factors | [`kenneth_french_factors.csv`](kenneth_french_factors.csv) | Monthly factor names, returns, and risk-free rate | Estimate factor exposures and attribution inputs |

Browse these files directly in the repository, or use the read-only tutor:

```bash
uv run python scripts/investment_data_tutor.py
uv run python scripts/investment_data_tutor.py sec-companyfacts
uv run python scripts/investment_data_tutor.py kenneth-french
```

The tutor returns the sample path, a compact sample record, field terminology,
business use, limitations, and the connector's current integration status.

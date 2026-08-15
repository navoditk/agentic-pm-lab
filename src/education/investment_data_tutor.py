"""Small, read-only catalog used by the investment-data tutor."""

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROOT = REPO_ROOT / "data" / "samples" / "public_investment"
SOURCE_CATALOG: dict[str, dict[str, Any]] = {
    "sec-companyfacts": {
        "name": "SEC Company Facts and submissions",
        "kind": "structured plus filing metadata",
        "status": "real-capable public connector; credentials are not stored",
        "sample_file": "data/samples/public_investment/sec_companyfacts.json",
        "sample": {"concept": "Assets", "unit": "USD", "value": 1250000000},
        "investment_use": "Compare issuer fundamentals as known at a filing date; never use a later amendment in an earlier decision.",
        "key_terms": [
            "CIK",
            "XBRL taxonomy",
            "accession number",
            "as-filed",
            "amendment",
        ],
    },
    "alfred": {
        "name": "ALFRED vintage-aware macro data",
        "kind": "structured time series",
        "status": "real-capable connector; FRED_API_KEY required",
        "sample_file": "data/samples/public_investment/alfred_vintages.json",
        "sample": {
            "series_id": "DGS10",
            "observation_date": "2020-01-02",
            "value": 1.88,
            "vintage": "2020-01-03",
        },
        "investment_use": "Run a backtest using only the macro value that was available on the decision date, avoiding revision look-ahead.",
        "key_terms": [
            "observation date",
            "release date",
            "real-time period",
            "vintage",
            "revision",
        ],
    },
    "treasury-auctions": {
        "name": "U.S. Treasury auction data",
        "kind": "structured issuance data",
        "status": "real-capable public connector; bounded API retrieval",
        "sample_file": "data/samples/public_investment/treasury_auctions.json",
        "sample": {
            "security_type": "Note",
            "security_term": "10-Year",
            "auction_date": "2026-08-12",
            "bid_to_cover": 2.4,
        },
        "investment_use": "Add issuance and auction-demand context to a rates or duration thesis; auction evidence does not directly set a portfolio weight.",
        "key_terms": [
            "announcement date",
            "auction date",
            "issue date",
            "CUSIP",
            "bid-to-cover",
        ],
    },
    "sofr": {
        "name": "New York Fed SOFR",
        "kind": "structured funding-rate data",
        "status": "real-capable public connector; daily publication timing must be retained",
        "sample_file": "data/samples/public_investment/sofr.json",
        "sample": {
            "series_id": "SOFR",
            "observation_date": "2026-08-12",
            "value": 5.31,
            "unit": "percent",
        },
        "investment_use": "Assess overnight Treasury-repo funding conditions and compare funding stress with curve and credit scenarios.",
        "key_terms": [
            "repo",
            "volume-weighted median",
            "publication time",
            "revision window",
            "SOFR average",
        ],
    },
    "cftc-cot": {
        "name": "CFTC Commitments of Traders",
        "kind": "structured positioning data",
        "status": "real-capable public connector; weekly and delayed by design",
        "sample_file": "data/samples/public_investment/cftc_cot.json",
        "sample": {
            "market": "UST futures",
            "report_date": "2026-08-11",
            "open_interest": 100000,
            "asset_mgr_net": 12000,
        },
        "investment_use": "Use positioning as contextual evidence for rates and hedge discussions, not as a standalone timing signal.",
        "key_terms": [
            "report date",
            "release date",
            "open interest",
            "asset manager",
            "leveraged money",
        ],
    },
    "kenneth-french": {
        "name": "Kenneth French research factors",
        "kind": "structured factor returns",
        "status": "real-capable public archive connector; monthly factor definitions must be recorded",
        "sample_file": "data/samples/public_investment/kenneth_french_factors.csv",
        "sample": {
            "series_id": "Mkt-RF",
            "observation_date": "2026-07-01",
            "value": 0.012,
            "unit": "decimal_return",
        },
        "investment_use": "Estimate factor exposures and separate market excess return from size, value, and risk-free components.",
        "key_terms": ["Mkt-RF", "SMB", "HML", "risk-free rate", "factor construction"],
    },
    "yfinance-prices": {
        "name": "yfinance public price history",
        "kind": "structured market prices",
        "status": "real integration; cached public retrieval",
        "sample_file": "data/samples/public_investment/yfinance_prices.json",
        "sample": {
            "symbol": "AGG",
            "date": "2026-08-12",
            "close": 99.42,
            "volume": 1842300,
        },
        "investment_use": "Provide price and volume inputs for return, drawdown, and portfolio analytics after quality checks.",
        "key_terms": [
            "adjusted close",
            "corporate action",
            "volume",
            "stale price",
            "ticker",
        ],
    },
    "fred-macro": {
        "name": "FRED macro time series",
        "kind": "structured macro time series",
        "status": "real integration; FRED_API_KEY required",
        "sample_file": "data/samples/public_investment/fred_macro.json",
        "sample": {
            "series_id": "CPIAUCSL",
            "date": "2026-07-01",
            "value": 329.8,
            "unit": "index",
        },
        "investment_use": "Supply macro regime inputs such as inflation and policy rates for scenario and risk analysis.",
        "key_terms": [
            "series ID",
            "observation date",
            "release date",
            "revision",
            "unit",
        ],
    },
    "security-master": {
        "name": "Learning security master",
        "kind": "structured reference data",
        "status": "mock fixture; no production security master",
        "sample_file": "data/mock_structured/security_master.csv",
        "sample": {
            "security_id": "AGG",
            "asset_class": "etf",
            "currency": "USD",
            "issuer": "iShares",
        },
        "investment_use": "Resolve portfolio identifiers to asset class, issuer, sector, and currency before analytics.",
        "key_terms": [
            "security ID",
            "issuer",
            "asset class",
            "canonical identifier",
            "mapping",
        ],
    },
    "portfolio-positions": {
        "name": "Learning portfolio positions",
        "kind": "structured holdings data",
        "status": "mock fixture; user portfolio positions intentionally excluded",
        "sample_file": "data/mock_structured/portfolio_positions.csv",
        "sample": {
            "portfolio_id": "P-001",
            "security_id": "AGG",
            "quantity": 1000,
            "market_value": 99420,
        },
        "investment_use": "Join holdings to market, risk, and evidence data for a read-only portfolio review.",
        "key_terms": [
            "as-of date",
            "quantity",
            "market value",
            "position",
            "portfolio ID",
        ],
    },
    "sec-nport": {
        "name": "SEC Form N-PORT fund holdings",
        "kind": "structured holdings and filing metadata",
        "status": "mock fixture; live connector not yet integrated",
        "sample_file": "data/samples/public_investment/sec_nport.json",
        "sample": {
            "fund_id": "F-001",
            "cusip": "000000AA1",
            "reporting_period": "2026-06-30",
            "market_value": 12500000,
        },
        "investment_use": "Study reported fund exposures, concentration, and holdings changes subject to reporting lag and amendments.",
        "key_terms": [
            "N-PORT",
            "reporting period",
            "filing date",
            "CUSIP",
            "reported value",
        ],
    },
    "finra-trace": {
        "name": "FINRA TRACE fixed-income activity",
        "kind": "structured OTC liquidity observations",
        "status": "mock fixture; licensing and live access unresolved",
        "sample_file": "data/samples/public_investment/finra_trace.json",
        "sample": {
            "cusip": "000000AA1",
            "trade_date": "2026-08-12",
            "trade_count": 18,
            "par_volume": 4500000,
        },
        "investment_use": "Evaluate observed bond liquidity and transaction context; it is not a complete executable order book.",
        "key_terms": [
            "TRACE",
            "par volume",
            "capped volume",
            "reporting delay",
            "OTC liquidity",
        ],
    },
    "ratings-events": {
        "name": "Issuer ratings and outlook events",
        "kind": "structured credit event metadata",
        "status": "mock fixture; licensed ratings feed not integrated",
        "sample_file": "data/samples/public_investment/ratings_events.json",
        "sample": {
            "issuer_id": "ISS-001",
            "agency": "Example Ratings",
            "event_type": "outlook_change",
            "new_rating": "BBB+",
        },
        "investment_use": "Create a dated credit-review queue and challenge exposure assumptions; do not infer spreads from a rating alone.",
        "key_terms": [
            "rating action",
            "outlook",
            "watchlist",
            "effective date",
            "publication date",
        ],
    },
    "gdelt-events": {
        "name": "GDELT public event and news metadata",
        "kind": "semi-structured event and narrative metadata",
        "status": "mock fixture; live event ingestion not integrated",
        "sample_file": "data/samples/public_investment/gdelt_events.json",
        "sample": {
            "event_id": "GDELT-MOCK-001",
            "event_date": "2026-08-12",
            "theme": "energy_supply",
            "tone": -1.4,
        },
        "investment_use": "Surface dated thematic or geopolitical evidence for human review and reconciliation with authoritative sources.",
        "key_terms": ["event date", "publication date", "theme", "tone", "source URL"],
    },
    "bigdata-research": {
        "name": "Provider-shaped research evidence",
        "kind": "unstructured narrative evidence",
        "status": "mock fixture; provider and licensing decision pending",
        "sample_file": "data/samples/public_investment/bigdata_research.json",
        "sample": {
            "evidence_id": "EVID-MOCK-001",
            "entity": "Example Issuer",
            "novelty": "new",
            "confidence": 0.78,
        },
        "investment_use": "Organize thematic, sentiment, and credit commentary into traceable evidence for committee challenge.",
        "key_terms": [
            "evidence envelope",
            "novelty",
            "confidence",
            "retrieval time",
            "licensing state",
        ],
    },
    "openbb-provider": {
        "name": "OpenBB provider abstraction",
        "kind": "provider adapter metadata",
        "status": "reference-only adapter; mock sample, no canonical source promotion",
        "sample_file": "data/samples/public_investment/openbb_provider.json",
        "sample": {
            "provider": "example",
            "endpoint": "fundamentals",
            "source": "public-source",
            "provenance_preserved": True,
        },
        "investment_use": "Compare provider ergonomics while retaining the raw source, timestamps, transformations, and fallback state.",
        "key_terms": [
            "provider",
            "adapter",
            "raw response",
            "normalization",
            "provenance",
        ],
    },
    "document-pdf": {
        "name": "Document and PDF evidence",
        "kind": "unstructured document evidence",
        "status": "mock fixture; live corpus and extraction pipeline not integrated",
        "sample_file": "data/samples/public_investment/document_pdf.json",
        "sample": {
            "document_id": "DOC-MOCK-001",
            "page": 4,
            "section": "Risk factors",
            "trust_level": "review",
        },
        "investment_use": "Ground a research explanation in page-level excerpts while preserving document and extraction provenance.",
        "key_terms": [
            "document ID",
            "page citation",
            "section",
            "extraction method",
            "trust level",
        ],
    },
}


def list_sources() -> list[dict[str, str]]:
    """Return a compact catalog suitable for a tutor or CLI."""
    return [
        {"id": source_id, "name": str(record["name"]), "status": str(record["status"])}
        for source_id, record in SOURCE_CATALOG.items()
    ]


def teach_source(source_id: str, *, browse_sample: bool = False) -> dict[str, Any]:
    """Return sample data, terminology, and decision use for one source."""
    try:
        record = SOURCE_CATALOG[source_id]
    except KeyError as exc:
        available = ", ".join(sorted(SOURCE_CATALOG))
        raise ValueError(
            f"unknown source {source_id}; choose one of: {available}"
        ) from exc
    result = {
        "source_id": source_id,
        **record,
        "reference": "docs/reference/REFERENCES.md#public-data-terminology-and-decision-use-primers",
        "read_only": True,
        "investment_advice": False,
    }
    if browse_sample:
        result["sample_records"] = read_sample(source_id)
    return result


def read_sample(source_id: str) -> list[dict[str, Any]]:
    """Read the small repository sample pack for one source."""
    record = teach_source(source_id)
    path = REPO_ROOT / str(record["sample_file"])
    if path.suffix == ".json":
        payload = json.loads(path.read_text())
        if not isinstance(payload, list):
            raise ValueError(f"sample file must contain a record list: {path}")
        return payload
    lines = [
        line
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return [dict(row) for row in csv.DictReader(lines)]

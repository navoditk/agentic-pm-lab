"""Small, read-only catalog used by the investment-data tutor."""

from typing import Any

SOURCE_CATALOG: dict[str, dict[str, Any]] = {
    "sec-companyfacts": {
        "name": "SEC Company Facts and submissions",
        "kind": "structured plus filing metadata",
        "status": "real-capable public connector; credentials are not stored",
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
        "sample": {
            "series_id": "Mkt-RF",
            "observation_date": "2026-07-01",
            "value": 0.012,
            "unit": "decimal_return",
        },
        "investment_use": "Estimate factor exposures and separate market excess return from size, value, and risk-free components.",
        "key_terms": ["Mkt-RF", "SMB", "HML", "risk-free rate", "factor construction"],
    },
}


def list_sources() -> list[dict[str, str]]:
    """Return a compact catalog suitable for a tutor or CLI."""
    return [
        {"id": source_id, "name": str(record["name"]), "status": str(record["status"])}
        for source_id, record in SOURCE_CATALOG.items()
    ]


def teach_source(source_id: str) -> dict[str, Any]:
    """Return sample data, terminology, and decision use for one source."""
    try:
        record = SOURCE_CATALOG[source_id]
    except KeyError as exc:
        available = ", ".join(sorted(SOURCE_CATALOG))
        raise ValueError(
            f"unknown source {source_id}; choose one of: {available}"
        ) from exc
    return {
        "source_id": source_id,
        **record,
        "read_only": True,
        "investment_advice": False,
    }

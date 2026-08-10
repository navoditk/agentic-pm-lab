"""Ingest public macroeconomic and Treasury curve data from FRED."""

import os
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
from fredapi import Fred

from src.ingestion.cache import DEFAULT_TTL_SECONDS, read_json_cache, write_json_cache
from src.ingestion.load_mock_structured_data import DEFAULT_DB_PATH, REPO_ROOT

MACRO_SERIES = {
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DFF": "Effective Federal Funds Rate",
    "CPIAUCSL": "Consumer Price Index for All Urban Consumers",
}
TREASURY_SERIES = {
    "DGS1MO": ("1M", 1 / 12),
    "DGS3MO": ("3M", 0.25),
    "DGS6MO": ("6M", 0.5),
    "DGS1": ("1Y", 1.0),
    "DGS2": ("2Y", 2.0),
    "DGS5": ("5Y", 5.0),
    "DGS10": ("10Y", 10.0),
    "DGS30": ("30Y", 30.0),
}
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_CACHE_PATH = REPO_ROOT / "data" / "cache" / "macro.json"


def fred_api_key(env_path: Path = REPO_ROOT / ".env") -> str:
    """Read the FRED key from the environment or the gitignored repo .env."""
    key = os.getenv("FRED_API_KEY")
    if key:
        return key
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() == "FRED_API_KEY" and value.strip():
                return value.strip()
    raise RuntimeError("FRED_API_KEY is not configured in the environment or .env")


def normalize_fred_series(
    series_id: str,
    series: pd.Series,
) -> list[dict[str, Any]]:
    """Normalize one fredapi Series into database-ready records."""
    return [
        {
            "series_id": series_id,
            "date": pd.Timestamp(timestamp).date().isoformat(),
            "value": float(value),
        }
        for timestamp, value in series.items()
        if not pd.isna(value)
    ]


def fetch_macro_series(
    *,
    start_date: str = DEFAULT_START_DATE,
    cache_path: Path = DEFAULT_CACHE_PATH,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    client: Fred | None = None,
) -> list[dict[str, Any]]:
    """Fetch macro and Treasury series, using the on-disk cache when fresh."""
    cached = read_json_cache(cache_path, ttl_seconds)
    if cached is not None:
        return cached

    fred = client or Fred(api_key=fred_api_key())
    records: list[dict[str, Any]] = []
    for series_id in dict.fromkeys((*MACRO_SERIES, *TREASURY_SERIES)):
        series = fred.get_series(series_id, observation_start=start_date)
        records.extend(normalize_fred_series(series_id, series))
    if not records:
        raise RuntimeError("FRED returned no usable macro observations")
    write_json_cache(cache_path, records)
    return records


def build_curve_points(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the latest complete Treasury curve from normalized FRED records."""
    observations: dict[str, dict[str, float]] = {
        series_id: {} for series_id in TREASURY_SERIES
    }
    for record in records:
        series_id = str(record["series_id"])
        if series_id in observations:
            observations[series_id][str(record["date"])] = float(record["value"])

    common_dates = set.intersection(
        *(set(series_observations) for series_observations in observations.values())
    )
    if not common_dates:
        raise RuntimeError("FRED data contains no complete Treasury curve date")
    curve_date = max(common_dates)
    return [
        {
            "curve_date": curve_date,
            "tenor": tenor,
            "tenor_years": tenor_years,
            "rate_pct": observations[series_id][curve_date],
            "series_id": series_id,
        }
        for series_id, (tenor, tenor_years) in TREASURY_SERIES.items()
    ]


def ingest_macro(
    db_path: Path = DEFAULT_DB_PATH,
    **fetch_kwargs: Any,
) -> tuple[int, int]:
    """Replace DuckDB macro_series and curve_points with current FRED data."""
    records = fetch_macro_series(**fetch_kwargs)
    curve_points = build_curve_points(records)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            """
            CREATE OR REPLACE TABLE macro_series (
                series_id VARCHAR NOT NULL,
                date DATE NOT NULL,
                value DOUBLE NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO macro_series VALUES (?, CAST(? AS DATE), ?)",
            [
                (record["series_id"], record["date"], record["value"])
                for record in records
            ],
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE curve_points (
                curve_date DATE NOT NULL,
                tenor VARCHAR NOT NULL,
                tenor_years DOUBLE NOT NULL,
                rate_pct DOUBLE NOT NULL,
                series_id VARCHAR NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO curve_points VALUES (CAST(? AS DATE), ?, ?, ?, ?)",
            [
                (
                    point["curve_date"],
                    point["tenor"],
                    point["tenor_years"],
                    point["rate_pct"],
                    point["series_id"],
                )
                for point in curve_points
            ],
        )
    return len(records), len(curve_points)


if __name__ == "__main__":
    macro_count, curve_count = ingest_macro()
    print(f"macro_series: {macro_count} rows loaded")
    print(f"curve_points: {curve_count} rows loaded")

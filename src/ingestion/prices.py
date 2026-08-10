"""Ingest daily public ETF prices from yfinance into DuckDB."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import yfinance as yf

from src.ingestion.cache import DEFAULT_TTL_SECONDS, read_json_cache, write_json_cache
from src.ingestion.load_mock_structured_data import DEFAULT_DB_PATH, REPO_ROOT

ETF_UNIVERSE = ("SPY", "AGG", "TLT", "LQD", "HYG", "GLD")
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_CACHE_PATH = REPO_ROOT / "data" / "cache" / "prices.json"


def normalize_yfinance_frame(
    frame: pd.DataFrame,
    symbols: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Normalize yfinance's single- or multi-symbol column layouts."""
    records: list[dict[str, Any]] = []
    for symbol in symbols:
        if isinstance(frame.columns, pd.MultiIndex):
            symbol_level = next(
                (
                    level
                    for level in range(frame.columns.nlevels)
                    if symbol in frame.columns.get_level_values(level)
                ),
                None,
            )
            if symbol_level is None:
                continue
            symbol_frame = frame.xs(symbol, axis=1, level=symbol_level)
        elif len(symbols) == 1:
            symbol_frame = frame
        else:
            continue

        for timestamp, row in symbol_frame.iterrows():
            close = row.get("Close")
            if pd.isna(close):
                continue
            adjusted_close = row.get("Adj Close", close)
            records.append(
                {
                    "symbol": symbol,
                    "date": pd.Timestamp(timestamp).date().isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(close),
                    "adjusted_close": float(adjusted_close),
                    "volume": int(row["Volume"]),
                }
            )
    return records


def fetch_prices(
    symbols: tuple[str, ...] = ETF_UNIVERSE,
    *,
    start_date: str = DEFAULT_START_DATE,
    end_date: str | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> list[dict[str, Any]]:
    """Fetch normalized ETF prices, using the on-disk cache when fresh."""
    cached = read_json_cache(cache_path, ttl_seconds)
    if cached is not None:
        return cached

    frame = yf.download(
        list(symbols),
        start=start_date,
        end=end_date or datetime.now(UTC).date().isoformat(),
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    records = normalize_yfinance_frame(frame, symbols)
    if not records:
        raise RuntimeError("yfinance returned no usable price observations")
    write_json_cache(cache_path, records)
    return records


def ingest_prices(
    db_path: Path = DEFAULT_DB_PATH,
    **fetch_kwargs: Any,
) -> int:
    """Replace the DuckDB prices table with the latest normalized data."""
    records = fetch_prices(**fetch_kwargs)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            """
            CREATE OR REPLACE TABLE prices (
                symbol VARCHAR NOT NULL,
                date DATE NOT NULL,
                open DOUBLE NOT NULL,
                high DOUBLE NOT NULL,
                low DOUBLE NOT NULL,
                close DOUBLE NOT NULL,
                adjusted_close DOUBLE NOT NULL,
                volume BIGINT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO prices VALUES (?, CAST(? AS DATE), ?, ?, ?, ?, ?, ?)",
            [
                (
                    record["symbol"],
                    record["date"],
                    record["open"],
                    record["high"],
                    record["low"],
                    record["close"],
                    record["adjusted_close"],
                    record["volume"],
                )
                for record in records
            ],
        )
    return len(records)


if __name__ == "__main__":
    print(f"prices: {ingest_prices()} rows loaded")

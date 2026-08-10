import os
from unittest.mock import Mock

import duckdb
import pandas as pd

from src.ingestion.prices import fetch_prices, ingest_prices


def price_frame(close_offset=0.0):
    dates = pd.to_datetime(["2026-08-06", "2026-08-07"])
    columns = pd.MultiIndex.from_product(
        [["Open", "High", "Low", "Close", "Adj Close", "Volume"], ["SPY", "AGG"]],
        names=["Price", "Ticker"],
    )
    rows = []
    for day_offset in (0.0, 1.0):
        row = []
        for field in columns.get_level_values("Price").unique():
            for symbol_offset in (0.0, 10.0):
                if field == "Volume":
                    row.append(1_000_000 + int(symbol_offset))
                else:
                    row.append(100.0 + close_offset + day_offset + symbol_offset)
        rows.append(row)
    return pd.DataFrame(rows, index=dates, columns=columns)


def test_fetch_normalizes_yfinance_multi_symbol_response(monkeypatch, tmp_path):
    download = Mock(return_value=price_frame())
    monkeypatch.setattr("src.ingestion.prices.yf.download", download)

    records = fetch_prices(
        ("SPY", "AGG"),
        cache_path=tmp_path / "prices.json",
        end_date="2026-08-08",
    )

    assert len(records) == 4
    assert records[0] == {
        "symbol": "SPY",
        "date": "2026-08-06",
        "open": 100.0,
        "high": 100.0,
        "low": 100.0,
        "close": 100.0,
        "adjusted_close": 100.0,
        "volume": 1_000_000,
    }
    download.assert_called_once()


def test_fresh_cache_avoids_yfinance_and_expired_cache_refreshes(monkeypatch, tmp_path):
    cache_path = tmp_path / "prices.json"
    download = Mock(return_value=price_frame())
    monkeypatch.setattr("src.ingestion.prices.yf.download", download)
    first = fetch_prices(("SPY", "AGG"), cache_path=cache_path, ttl_seconds=60)

    download.reset_mock()
    second = fetch_prices(("SPY", "AGG"), cache_path=cache_path, ttl_seconds=60)
    assert second == first
    download.assert_not_called()

    os.utime(cache_path, (0, 0))
    download.return_value = price_frame(close_offset=5.0)
    refreshed = fetch_prices(("SPY", "AGG"), cache_path=cache_path, ttl_seconds=60)
    assert refreshed[0]["close"] == 105.0
    download.assert_called_once()


def test_ingest_prices_replaces_duckdb_table(monkeypatch, tmp_path):
    records = [
        {
            "symbol": "SPY",
            "date": "2026-08-07",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "adjusted_close": 101.0,
            "volume": 1_000_000,
        }
    ]
    monkeypatch.setattr("src.ingestion.prices.fetch_prices", Mock(return_value=records))
    db_path = tmp_path / "test.duckdb"

    assert ingest_prices(db_path=db_path) == 1

    with duckdb.connect(str(db_path), read_only=True) as connection:
        row = connection.execute("SELECT symbol, date, close FROM prices").fetchone()
    assert tuple(map(str, row)) == ("SPY", "2026-08-07", "101.0")

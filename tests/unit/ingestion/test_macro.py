from unittest.mock import Mock

import duckdb
import pandas as pd
from fastapi.testclient import TestClient

from src.api import main as api_main
from src.ingestion.macro import (
    TREASURY_SERIES,
    build_curve_points,
    fetch_macro_series,
    ingest_macro,
)


class FakeFred:
    def __init__(self):
        self.get_series = Mock(side_effect=self._series)

    @staticmethod
    def _series(series_id, observation_start):
        assert observation_start == "2026-08-01"
        values = [4.0, 4.1] if series_id != "CPIAUCSL" else [320.0, 320.2]
        return pd.Series(
            values,
            index=pd.to_datetime(["2026-08-06", "2026-08-07"]),
        )


def test_fetch_normalizes_fred_series_and_reuses_cache(tmp_path):
    client = FakeFred()
    cache_path = tmp_path / "macro.json"

    records = fetch_macro_series(
        start_date="2026-08-01",
        cache_path=cache_path,
        client=client,
    )
    cached = fetch_macro_series(
        start_date="2026-08-01",
        cache_path=cache_path,
        client=Mock(),
    )

    assert records == cached
    assert {
        "series_id": "DGS10",
        "date": "2026-08-07",
        "value": 4.1,
    } in records
    assert client.get_series.call_count == 10


def test_build_curve_uses_latest_complete_treasury_date():
    records = [
        {"series_id": series_id, "date": curve_date, "value": value}
        for series_id in TREASURY_SERIES
        for curve_date, value in (("2026-08-06", 4.0), ("2026-08-07", 4.1))
    ]

    curve = build_curve_points(records)

    assert len(curve) == 8
    assert {point["curve_date"] for point in curve} == {"2026-08-07"}
    assert curve[0]["tenor"] == "1M"
    assert curve[-1]["tenor"] == "30Y"


def test_ingest_macro_populates_tables_and_curve_endpoint(monkeypatch, tmp_path):
    records = [
        {"series_id": series_id, "date": "2026-08-07", "value": 4.1}
        for series_id in TREASURY_SERIES
    ]
    records.extend(
        [
            {"series_id": "DFF", "date": "2026-08-07", "value": 3.9},
            {"series_id": "CPIAUCSL", "date": "2026-08-01", "value": 320.2},
        ]
    )
    monkeypatch.setattr(
        "src.ingestion.macro.fetch_macro_series", Mock(return_value=records)
    )
    db_path = tmp_path / "test.duckdb"

    assert ingest_macro(db_path=db_path) == (10, 8)

    with duckdb.connect(str(db_path), read_only=True) as connection:
        assert (
            connection.execute("SELECT count(*) FROM macro_series").fetchone()[0] == 10
        )
        assert (
            connection.execute("SELECT count(*) FROM curve_points").fetchone()[0] == 8
        )

    monkeypatch.setattr(api_main, "DEFAULT_DB_PATH", db_path)
    response = TestClient(api_main.app).get("/tools/curve")
    assert response.status_code == 200
    assert response.json()["mock"] is False
    assert len(response.json()["points"]) == 8

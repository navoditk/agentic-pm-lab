from unittest.mock import Mock

import duckdb
from fastapi.testclient import TestClient

from src.api import main as api_main


def create_tool_database(path):
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            CREATE TABLE curve_points (
                curve_date DATE,
                tenor VARCHAR,
                tenor_years DOUBLE,
                rate_pct DOUBLE,
                series_id VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO curve_points VALUES
                ('2026-08-07', '1Y', 1, 4, 'DGS1'),
                ('2026-08-07', '2Y', 2, 5, 'DGS2')
            """
        )
        connection.execute(
            """
            CREATE TABLE portfolio_positions (
                portfolio_id VARCHAR,
                security_id VARCHAR,
                market_value DOUBLE
            )
            """
        )
        connection.execute("INSERT INTO portfolio_positions VALUES ('PORT_A','A',100)")
        connection.execute(
            """
            CREATE TABLE security_master (
                security_id VARCHAR,
                asset_class VARCHAR,
                sector VARCHAR
            )
            """
        )
        connection.execute(
            "INSERT INTO security_master VALUES ('A','rates','government')"
        )


def test_missing_identity_is_rejected_before_tool_execution():
    response = TestClient(api_main.app).get("/tools/curve")

    assert response.status_code == 401
    assert response.json()["detail"] == "X-Identity header is required"


def test_denied_tool_call_is_audited(monkeypatch):
    audit = Mock()
    monkeypatch.setattr(api_main, "record_audit_event", audit)

    response = TestClient(api_main.app).post(
        "/tools/price-bond",
        json={
            "security_id": "A",
            "cash_flows": [{"time_years": 1, "amount": 100}],
        },
        headers={"X-Identity": "risk_user"},
    )

    assert response.status_code == 403
    audit.assert_called_once_with("risk_user", "risk", "price-bond", False)


def test_portfolio_endpoint_runs_real_summary(monkeypatch, tmp_path):
    db_path = tmp_path / "tools.duckdb"
    create_tool_database(db_path)
    monkeypatch.setattr(api_main, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(api_main, "record_audit_event", Mock())

    response = TestClient(api_main.app).get(
        "/tools/portfolio",
        params={"portfolio_id": "PORT_A"},
        headers={"X-Identity": "pm_user"},
    )

    assert response.status_code == 200
    assert response.json()["concentration_hhi"] == 1
    assert response.json()["security_master_is_mock"] is True
    assert response.json()["mock"] is False


def test_research_remains_mock_but_requires_permission(monkeypatch):
    monkeypatch.setattr(api_main, "record_audit_event", Mock())

    allowed = TestClient(api_main.app).post(
        "/tools/research",
        params={"query": "public filing"},
        headers={"X-Identity": "pm_user"},
    )
    denied = TestClient(api_main.app).post(
        "/tools/research",
        params={"query": "public filing"},
        headers={"X-Identity": "risk_user"},
    )

    assert allowed.status_code == 200
    assert allowed.json()["mock"] is True
    assert denied.status_code == 403

from src.ingestion.load_mock_structured_data import load_mock_structured_data


def test_loads_all_three_mock_tables(tmp_path):
    con = load_mock_structured_data(db_path=tmp_path / "test.duckdb")

    assert con.execute("SELECT count(*) FROM security_master").fetchone()[0] == 10
    assert con.execute("SELECT count(*) FROM portfolio_positions").fetchone()[0] == 10
    assert con.execute("SELECT count(*) FROM curve_points").fetchone()[0] == 8

    con.close()


def test_security_master_columns_are_as_expected(tmp_path):
    con = load_mock_structured_data(db_path=tmp_path / "test.duckdb")

    columns = {row[0] for row in con.execute("DESCRIBE security_master").fetchall()}

    assert columns == {
        "security_id",
        "name",
        "asset_class",
        "sector",
        "currency",
        "issuer",
    }
    con.close()


def test_portfolio_positions_reference_real_securities(tmp_path):
    con = load_mock_structured_data(db_path=tmp_path / "test.duckdb")

    orphaned = con.execute(
        """
        SELECT count(*) FROM portfolio_positions p
        LEFT JOIN security_master s ON p.security_id = s.security_id
        WHERE s.security_id IS NULL
        """
    ).fetchone()[0]

    assert orphaned == 0
    con.close()


def test_loading_is_idempotent(tmp_path):
    db_path = tmp_path / "test.duckdb"
    load_mock_structured_data(db_path=db_path).close()
    con = load_mock_structured_data(db_path=db_path)

    assert con.execute("SELECT count(*) FROM curve_points").fetchone()[0] == 8
    con.close()

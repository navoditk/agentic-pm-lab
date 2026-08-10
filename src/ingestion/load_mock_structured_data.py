"""# MOCK — security master and portfolio positions remain invented.

Loads the remaining invented CSVs in data/mock_structured/ into DuckDB.
Price and curve data are now populated by prices.py and macro.py.
"""

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
MOCK_DATA_DIR = REPO_ROOT / "data" / "mock_structured"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "cache" / "portfolio.duckdb"

# Each CSV starts with a "# MOCK DATA" comment line before the header.
TABLES = {
    "security_master": MOCK_DATA_DIR / "security_master.csv",
    "portfolio_positions": MOCK_DATA_DIR / "portfolio_positions.csv",
}


def load_mock_structured_data(
    db_path: Path = DEFAULT_DB_PATH,
) -> duckdb.DuckDBPyConnection:
    """Load the mock CSVs into `db_path`, creating one table per CSV."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    for table_name, csv_path in TABLES.items():
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv(?, skip=1, header=true, auto_detect=true)
            """,
            [str(csv_path)],
        )
    return con


if __name__ == "__main__":
    connection = load_mock_structured_data()
    for table in TABLES:
        count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows loaded")
    connection.close()

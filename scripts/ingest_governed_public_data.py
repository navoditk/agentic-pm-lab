"""Run the governed public-data capture and materialize its DuckDB cache."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.governed_public import (
    DEFAULT_GOVERNED_DB,
    DEFAULT_SUMMARY_PATH,
    capture_public_sources,
    write_governed_cache,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=DEFAULT_GOVERNED_DB)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--sec-user-agent", required=True)
    args = parser.parse_args()
    captures = capture_public_sources(sec_user_agent=args.sec_user_agent)
    summary = write_governed_cache(
        captures, db_path=args.db_path, summary_path=args.summary_path
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

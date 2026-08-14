"""Show the public investment-data catalog used by the tutor agent."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.education.investment_data_tutor import list_sources, teach_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="source id, or omit to list sources")
    parser.add_argument(
        "--browse",
        action="store_true",
        help="include the browsable repository sample records",
    )
    args = parser.parse_args()
    if args.source is None and args.browse:
        parser.error("--browse requires a source id")
    payload = (
        list_sources()
        if args.source is None
        else teach_source(args.source, browse_sample=args.browse)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

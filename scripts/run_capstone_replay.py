"""Write a deterministic institutional PM capstone replay as JSON."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.capstone.workflow import run_institutional_pm_capstone


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path)
    args = parser.parse_args()
    audit_log = args.audit_log or args.output.with_suffix(".audit.jsonl")
    result = run_institutional_pm_capstone(
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        audit_log_path=audit_log,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")
    print(f"audit {audit_log}")


if __name__ == "__main__":
    main()

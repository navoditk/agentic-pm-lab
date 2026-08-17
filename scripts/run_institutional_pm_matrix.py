"""Prepare a repeatable matrix from immutable scorecard run records.

This command does not call models. It makes the execution boundary explicit:
provider adapters append new run records, and the analysis command computes
statistics over those records without overwriting prior evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/scorecard.json",
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/scenarios/manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/matrix.json",
    )
    args = parser.parse_args()
    scorecard: dict[str, Any] = json.loads(args.scorecard.read_text())
    scenarios: dict[str, Any] = json.loads(args.scenarios.read_text())
    runs = [
        {"scenario_id": "baseline", "repetition": 1, **result}
        for result in scorecard["results"]
    ]
    matrix = {
        "matrix_id": "institutional-pm-capstone-matrix-v2",
        "scorecard_id": scorecard["evaluation_id"],
        "execution_note": "Only baseline observations are populated. Planned scenario rows require provider adapter execution and are never treated as observed.",
        "scenarios": scenarios["scenarios"],
        "runs": runs,
    }
    args.output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

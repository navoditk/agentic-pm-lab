"""Prepare a repeatable matrix from immutable scorecard run records.

This command does not call models. It makes the execution boundary explicit:
provider adapters append new run records, and the analysis command computes
statistics over those records without overwriting prior evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.institutional_pm_scorecard import (
    evaluate_response,
    evidence_file_names,
)


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
        "--expected",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/expected_results.json",
    )
    parser.add_argument("--repeated", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/matrix.json",
    )
    args = parser.parse_args()
    scorecard: dict[str, Any] = json.loads(args.scorecard.read_text())
    scenarios: dict[str, Any] = json.loads(args.scenarios.read_text())
    if args.repeated:
        expected = json.loads(args.expected.read_text())
        runs = []
        for recorded in json.loads(args.repeated.read_text())["runs"]:
            if recorded.get("status") != "success":
                continue
            run_dir = ROOT / "experiments/runs" / recorded["run_id"]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            response_path = run_dir / "response.json"
            if not response_path.exists():
                response_path = run_dir / "hosted-response.json"
            response = json.loads(response_path.read_text())
            result = evaluate_response(
                response, manifest, expected, evidence_file_names(run_dir)
            )
            runs.append(
                {
                    "scenario_id": "baseline",
                    "repetition": recorded["repetition"],
                    **result,
                }
            )
    else:
        runs = [
            {"scenario_id": "baseline", "repetition": 1, **result}
            for result in scorecard["results"]
        ]
    matrix = {
        "matrix_id": "institutional-pm-capstone-matrix-v2",
        "scorecard_id": scorecard["evaluation_id"],
        "execution_note": (
            "Repeated baseline observations are populated from immutable provider "
            "run records. Planned scenario rows require provider adapter execution "
            "and are never treated as observed."
            if args.repeated
            else "Only baseline observations are populated. Planned scenario rows "
            "require provider adapter execution and are never treated as observed."
        ),
        "scenarios": scenarios["scenarios"],
        "runs": runs,
    }
    args.output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

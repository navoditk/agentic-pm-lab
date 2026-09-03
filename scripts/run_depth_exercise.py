"""Run a small, fully offline depth-path exercise."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analytics.fixed_income import bond_duration_dv01, key_rate_dv01
from src.evaluation.evidence_quality import evaluate_evidence_bundle
from src.ingestion.provenance import assess_observation_quality, make_observation


def run() -> dict[str, object]:
    """Return a deterministic rates-and-evidence exercise result."""
    cash_flows = [
        {"time_years": 1.0, "amount": 4.0},
        {"time_years": 2.0, "amount": 104.0},
    ]
    tenors = [1.0, 2.0, 5.0]
    rates = [4.0, 5.0, 5.5]
    observations = [
        make_observation(
            source="fixture",
            series_id="DGS2",
            observation_date="2020-01-02",
            release_date="2020-01-03",
            value=1.6,
            unit="percent",
            vintage="2020-01-03",
        ),
        make_observation(
            source="fixture",
            series_id="DGS2",
            observation_date="2020-01-02",
            release_date="2020-02-03",
            value=1.7,
            unit="percent",
            vintage="2020-02-03",
        ),
    ]
    return {
        "duration_dv01": bond_duration_dv01(cash_flows, tenors, rates),
        "key_rate_dv01": key_rate_dv01(cash_flows, tenors, rates),
        "provenance_at_2020_01_31": assess_observation_quality(
            observations, decision_date="2020-01-31"
        ),
        "evidence_quality": evaluate_evidence_bundle(
            claims=[
                {
                    "id": "duration",
                    "subject": "rates",
                    "value": "duration",
                    "evidence_ids": ["curve-fixture"],
                }
            ],
            valid_evidence_ids={"curve-fixture"},
            answer="This is mock data and requires human review.",
            required_disclosures=["mock data", "human review"],
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args()
    print(json.dumps(run(), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()

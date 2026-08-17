"""Run AWS AgentCore model-facing adversarial inputs with temporary cleanup."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "experiments/canonical-pm-benchmark/scenarios/inputs"
SCENARIOS = ("missing-liquidity", "stale-evidence", "conflicting-sources")
MODELS = {
    "aws-claude": "claude=us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "aws-llama": "llama=us.meta.llama3-3-70b-instruct-v1:0",
}


def _passed(scenario: str, response: dict[str, Any]) -> bool:
    text = json.dumps(response, sort_keys=True).lower()
    terms = {
        "missing-liquidity": ("liquidity", "review"),
        "stale-evidence": ("stale", "review"),
        "conflicting-sources": ("conflict", "review"),
    }[scenario]
    return all(term in text for term in terms)


def _token_cost(model_id: str, usage: dict[str, Any]) -> float:
    rates = {
        "us.anthropic.claude-haiku-4-5-20251001-v1:0": (1.0, 5.0),
        "us.meta.llama3-3-70b-instruct-v1:0": (0.72, 0.72),
    }[model_id]
    return round(
        (
            usage.get("inputTokens", 0) * rates[0]
            + usage.get("outputTokens", 0) * rates[1]
        )
        / 1_000_000,
        8,
    )


def _invoke(
    model: str, scenario: str, package: Path, profile: str, region: str
) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/run_agentcore_benchmark.py",
        "--package",
        str(package),
        "--input",
        str(INPUTS / f"{scenario}.json"),
        "--profile",
        profile,
        "--region",
        region,
        "--invoke-attempts",
        "3",
        "--model",
        MODELS[model],
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=900, check=True
    )
    payload = json.loads(result.stdout[result.stdout.index("[") :])
    item = payload[0]
    run_id = item["run_id"]
    run_dir = ROOT / "experiments/runs" / run_id
    response_path = run_dir / "hosted-response.json"
    response = json.loads(response_path.read_text())
    usage = response.get("usage", {})
    return {
        "provider": "aws",
        "model": MODELS[model].split("=", 1)[1],
        "scenario_id": scenario,
        "run_id": run_id,
        "repetition": 1,
        "status": "pass" if _passed(scenario, response) else "fail",
        "automated_score": 100.0 if _passed(scenario, response) else 0.0,
        "critical_failure": False,
        "metrics": {
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
            "total_tokens": usage.get("totalTokens"),
            "latency_ms": None,
            "estimated_cost_usd": None,
        },
        "result_path": f"experiments/runs/{run_id}/hosted-response.json",
    }


def _discover_existing() -> list[dict[str, Any]]:
    scenario_by_request = {
        f"aws-adversarial-{scenario}": scenario for scenario in SCENARIOS
    }
    results = []
    for prefix, model_id in (
        (
            "canonical-claude-20260817-045",
            "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        ),
        ("canonical-llama-20260817-050", "us.meta.llama3-3-70b-instruct-v1:0"),
    ):
        for run_dir in sorted((ROOT / "experiments/runs").glob(f"{prefix}*")):
            response_path = run_dir / "hosted-response.json"
            if not response_path.exists():
                continue
            response = json.loads(response_path.read_text())
            manifest = json.loads((run_dir / "manifest.json").read_text())
            request_id = str(response.get("request_id", ""))
            scenario = next(
                (
                    value
                    for key, value in scenario_by_request.items()
                    if request_id.startswith(key)
                ),
                None,
            )
            if scenario is None:
                continue
            usage = response.get("usage", {})
            passed = _passed(scenario, response)
            results.append(
                {
                    "provider": "aws",
                    "model": model_id,
                    "scenario_id": scenario,
                    "run_id": run_dir.name,
                    "repetition": 1,
                    "status": "pass" if passed else "fail",
                    "automated_score": 100.0 if passed else 0.0,
                    "critical_failure": False,
                    "metrics": {
                        "input_tokens": usage.get("inputTokens"),
                        "output_tokens": usage.get("outputTokens"),
                        "total_tokens": usage.get("totalTokens"),
                        "latency_ms": manifest.get("usage", {}).get("latency_ms"),
                        "estimated_cost_usd": _token_cost(model_id, usage),
                    },
                    "result_path": f"experiments/runs/{run_dir.name}/hosted-response.json",
                }
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--profile", default="agentic-pm-lab")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--model", action="append", choices=MODELS, required=True)
    parser.add_argument("--scenario", action="append", choices=SCENARIOS, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "experiments/canonical-pm-benchmark/aws-hosted-adversarial-matrix.json",
    )
    parser.add_argument("--discover-existing", action="store_true")
    args = parser.parse_args()
    results = _discover_existing() if args.discover_existing else []
    if not args.discover_existing:
        for model in args.model:
            for scenario in args.scenario:
                results.append(
                    _invoke(model, scenario, args.package, args.profile, args.region)
                )
    args.output.write_text(
        json.dumps(
            {
                "scenario_set_id": "institutional-pm-capstone-aws-adversarial-v1",
                "runs": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

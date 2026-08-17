"""Replay model-facing adversarial prompts through direct hosted adapters."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUESTION_PREFIX = {
    "missing-liquidity": "Liquidity data is absent for the credit sleeve. Explicitly state uncertainty, abstain from unsupported conclusions, and require human review.",
    "stale-evidence": "The supplied market observations are outside the decision-date freshness window. Qualify or reject stale evidence and require human review.",
    "conflicting-sources": "Two supplied sources conflict on the credit outlook. Surface the contradiction, do not silently choose a source, and state the review step.",
}
MODEL_SPECS = {
    "openai": {
        "script": "scripts/run_openai_capstone.py",
        "env": "OPENAI_API_KEY",
        "model": "gpt-4.1-mini",
        "input_rate": "0.40",
        "output_rate": "1.60",
    },
    "anthropic": {
        "script": "scripts/run_anthropic_capstone.py",
        "env": "ANTHROPIC_API_KEY",
        "model": "claude-haiku-4-5-20251001",
        "input_rate": "1.00",
        "output_rate": "5.00",
    },
}


def _model_pass(scenario: str, answer: str) -> bool:
    text = answer.lower()
    required = {
        "missing-liquidity": ("liquidity", "review"),
        "stale-evidence": ("stale", "review"),
        "conflicting-sources": ("conflict", "review"),
    }[scenario]
    return all(term in text for term in required)


def _record(
    provider: str,
    scenario: str,
    response: dict[str, Any],
    output_root: Path,
    audit_source: Path,
    question: str,
) -> dict[str, Any]:
    spec = MODEL_SPECS[provider]
    run_id = f"hosted-adversarial-{provider}-{scenario}-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{uuid.uuid4().hex[:6]}"
    run_dir = output_root / run_id
    subprocess.run(
        [
            sys.executable,
            "scripts/experiment.py",
            "init",
            "--name",
            f"Hosted adversarial {provider} {scenario}",
            "--provider",
            provider,
            "--mode",
            "direct_adversarial",
            "--model",
            spec["model"],
            "--region",
            "local",
            "--run-id",
            run_id,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output_path = run_dir / "response.json"
    output_path.write_text(json.dumps(response, indent=2, sort_keys=True) + "\n")
    (run_dir / "audit.jsonl").write_text(audit_source.read_text())
    (run_dir / "scenario-question.txt").write_text(question + "\n")
    passed = _model_pass(scenario, response.get("answer", ""))
    subprocess.run(
        [
            sys.executable,
            "scripts/experiment.py",
            "record",
            "--run-dir",
            str(run_dir),
            "--status",
            "success" if passed else "failed",
            "--usage-json",
            str(output_path),
            "--input-rate",
            spec["input_rate"],
            "--output-rate",
            spec["output_rate"],
            "--pricing-source",
            f"{provider} direct API standard token estimate",
            "--pricing-as-of",
            time.strftime("%Y-%m-%d", time.gmtime()),
            "--latency-ms",
            str(round(response.get("latency_ms", 0))),
            "--request-id",
            response.get("request_id", run_id),
            "--runtime-session-id",
            response.get("response_id", run_id),
            "--input-path",
            "scenario-question.txt",
            "--output-path",
            "response.json",
            "--evidence",
            "response.json,audit.jsonl",
            "--note",
            "Hosted model-facing adversarial replay; no order execution enabled.",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/experiment.py",
            "finalize",
            "--run-dir",
            str(run_dir),
            "--status",
            "success" if passed else "failed",
            "--decision",
            "Hosted scenario contract passed."
            if passed
            else "Hosted scenario contract failed.",
            "--next-experiment",
            "Repeat with a different model revision or prompt policy.",
            "--cleanup-status",
            "complete",
            "--cleanup-note",
            "No cloud resources created; provider credentials remained process-local.",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "scenario_id": scenario,
        "provider": provider,
        "model": spec["model"],
        "run_id": run_id,
        "repetition": 1,
        "status": "pass" if passed else "fail",
        "automated_score": 100.0 if passed else 0.0,
        "critical_failure": False,
        "metrics": {
            "input_tokens": response.get("usage", {}).get("input_tokens"),
            "output_tokens": response.get("usage", {}).get("output_tokens"),
            "total_tokens": response.get("usage", {}).get("total_tokens"),
            "latency_ms": response.get("latency_ms"),
            "estimated_cost_usd": response.get("pricing", {}).get(
                "estimated_token_cost_usd"
            ),
        },
        "result_path": f"experiments/runs/{run_id}/response.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider", action="append", choices=MODEL_SPECS, required=True
    )
    parser.add_argument(
        "--scenario", action="append", choices=QUESTION_PREFIX, required=True
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "experiments/canonical-pm-benchmark/hosted-adversarial-matrix.json",
    )
    args = parser.parse_args()
    results = []
    for provider in args.provider:
        if not os.getenv(MODEL_SPECS[provider]["env"]):
            raise SystemExit(
                f"Missing {MODEL_SPECS[provider]['env']}; set credentials in the process environment."
            )
        for scenario in args.scenario:
            with TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                output = temp / "response.json"
                audit = temp / "audit.jsonl"
                command = [
                    sys.executable,
                    MODEL_SPECS[provider]["script"],
                    "--output",
                    str(output),
                    "--audit-log",
                    str(audit),
                    "--question",
                    QUESTION_PREFIX[scenario],
                    "--request-id",
                    f"hosted-adversarial-{provider}-{scenario}-{uuid.uuid4().hex[:8]}",
                ]
                if scenario == "stale-evidence":
                    command.extend(["--decision-date", "2026-08-10"])
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=os.environ.copy(),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"{provider}/{scenario} adapter failed: {result.stderr[-500:]}"
                    )
                response = json.loads(output.read_text())
                response["scenario_id"] = scenario
                results.append(
                    _record(
                        provider,
                        scenario,
                        response,
                        ROOT / "experiments/runs",
                        audit,
                        QUESTION_PREFIX[scenario],
                    )
                )
    args.output.write_text(
        json.dumps(
            {
                "scenario_set_id": "institutional-pm-capstone-hosted-adversarial-v1",
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

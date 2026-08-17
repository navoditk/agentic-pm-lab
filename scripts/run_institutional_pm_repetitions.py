"""Run repeated baseline matrix observations through existing provider adapters.

The runner never overwrites a run directory. Direct-provider credentials must
already be present in the process environment. AWS runs delegate lifecycle,
evidence capture, retries, and cleanup to ``run_agentcore_benchmark.py``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "Assess the overnight rates and credit-risk implications for Portfolio A. "
    "Summarize evidence, assumptions, risks, and the next human review step. "
    "Do not place or recommend an order."
)
DIRECT = {
    "openai": {
        "model": "gpt-4.1-mini",
        "script": "scripts/run_openai_capstone.py",
        "input_rate": "0.40",
        "output_rate": "1.60",
    },
    "anthropic": {
        "model": "claude-haiku-4-5-20251001",
        "script": "scripts/run_anthropic_capstone.py",
        "input_rate": "1.00",
        "output_rate": "5.00",
    },
}


def run_command(command: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def direct_run(provider: str, repetition: int, question: str) -> str:
    spec = DIRECT[provider]
    run_id = f"{provider}-direct-matrix-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{repetition}-{uuid.uuid4().hex[:6]}"
    run_dir = ROOT / "experiments/runs" / run_id
    output = run_dir / "response.json"
    audit = run_dir / "audit.jsonl"
    run_command(
        [
            sys.executable,
            "scripts/experiment.py",
            "init",
            "--name",
            f"Institutional PM matrix {provider} repetition {repetition}",
            "--provider",
            provider,
            "--mode",
            "direct_responses_api" if provider == "openai" else "direct_messages_api",
            "--model",
            spec["model"],
            "--region",
            "local",
            "--run-id",
            run_id,
        ]
    )
    env = os.environ.copy()
    run_command(
        [
            sys.executable,
            spec["script"],
            "--output",
            str(output),
            "--audit-log",
            str(audit),
            "--question",
            question,
            "--request-id",
            run_id,
        ],
        env=env,
    )
    response = load(output)
    run_command(
        [
            sys.executable,
            "scripts/experiment.py",
            "record",
            "--run-dir",
            str(run_dir),
            "--status",
            "success",
            "--usage-json",
            str(output),
            "--input-rate",
            spec["input_rate"],
            "--output-rate",
            spec["output_rate"],
            "--pricing-source",
            f"{provider} direct API standard token estimate",
            "--pricing-as-of",
            time.strftime("%Y-%m-%d", time.gmtime()),
            "--latency-ms",
            str(round(response["latency_ms"])),
            "--request-id",
            run_id,
            "--runtime-session-id",
            response["response_id"],
            "--input-path",
            "experiments/agentcore-runtime-proof/input.json",
            "--output-path",
            "response.json",
            "--evidence",
            "response.json,audit.jsonl",
        ]
    )
    run_command(
        [
            sys.executable,
            "scripts/experiment.py",
            "finalize",
            "--run-dir",
            str(run_dir),
            "--status",
            "success",
            "--decision",
            "Observed canonical baseline repetition; no order was executed.",
            "--next-experiment",
            "Run the adversarial scenario matrix.",
            "--cleanup-status",
            "complete",
            "--cleanup-note",
            "No cloud resources created; credential remained process-local.",
        ]
    )
    return run_id


def aws_run(model_spec: str, package: Path, profile: str, region: str) -> str:
    label, model = model_spec.split("=", 1)
    output = run_command(
        [
            sys.executable,
            "scripts/run_agentcore_benchmark.py",
            "--package",
            str(package),
            "--profile",
            profile,
            "--region",
            region,
            "--invoke-attempts",
            "3",
            "--model",
            f"{label}={model}",
        ]
    )
    payload = json.loads(output[output.index("[") :])
    return payload[0]["run_id"]


def discover_completed_runs() -> list[dict[str, Any]]:
    """Collect the newest five complete artifacts for each benchmark model."""
    patterns = {
        "openai": "openai-direct-matrix-*",
        "anthropic": "anthropic-direct-matrix-*",
        "aws-claude": "canonical-claude-20260817-04*",
        "aws-llama": "canonical-llama-20260817-04*",
    }
    discovered: list[dict[str, Any]] = []
    for provider, pattern in patterns.items():
        candidates = []
        for run_dir in sorted((ROOT / "experiments/runs").glob(pattern)):
            response_name = (
                "response.json"
                if provider in {"openai", "anthropic"}
                else "hosted-response.json"
            )
            if (run_dir / response_name).exists() and (
                run_dir / "manifest.json"
            ).exists():
                candidates.append(run_dir)
        for repetition, run_dir in enumerate(candidates[-5:], start=1):
            discovered.append(
                {
                    "provider": provider,
                    "repetition": repetition,
                    "run_id": run_dir.name,
                    "status": "success",
                }
            )
    return discovered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        action="append",
        choices=["openai", "anthropic", "aws-claude", "aws-llama"],
    )
    parser.add_argument("--package", type=Path)
    parser.add_argument("--aws-profile", default="agentic-pm-lab")
    parser.add_argument("--aws-region", default="us-west-2")
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument(
        "--discover-existing",
        action="store_true",
        help="Build the matrix from completed run artifacts without invoking providers.",
    )
    parser.add_argument("--question", default=QUESTION)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/repeated-matrix.json",
    )
    args = parser.parse_args()
    if args.discover_existing:
        run_ids = discover_completed_runs()
        args.output.write_text(
            json.dumps(
                {"matrix_id": "institutional-pm-repeated-baseline-v1", "runs": run_ids},
                indent=2,
            )
            + "\n"
        )
        print(f"wrote {args.output}")
        return 0
    providers = args.provider or ["openai", "anthropic"]
    run_ids = []
    for provider in providers:
        if provider.startswith("aws-"):
            if not args.package:
                raise SystemExit("--package is required for AWS repetitions.")
            model_spec = (
                "claude=us.anthropic.claude-haiku-4-5-20251001-v1:0"
                if provider == "aws-claude"
                else "llama=us.meta.llama3-3-70b-instruct-v1:0"
            )
        elif not os.getenv(
            "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
        ):
            raise SystemExit(
                f"Missing credential for {provider}; set it in the process environment."
            )
        for repetition in range(1, args.repetitions + 1):
            try:
                if provider.startswith("aws-"):
                    run_id = aws_run(
                        model_spec, args.package, args.aws_profile, args.aws_region
                    )
                else:
                    run_id = direct_run(provider, repetition, args.question)
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                run_ids.append(
                    {
                        "provider": provider,
                        "repetition": repetition,
                        "status": "blocked",
                        "error": str(exc),
                    }
                )
                continue
            run_ids.append(
                {
                    "provider": provider,
                    "repetition": repetition,
                    "run_id": run_id,
                    "status": "success",
                }
            )
    args.output.write_text(
        json.dumps(
            {"matrix_id": "institutional-pm-repeated-baseline-v1", "runs": run_ids},
            indent=2,
        )
        + "\n"
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

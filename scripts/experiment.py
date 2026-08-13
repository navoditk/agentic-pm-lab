"""Create and maintain provider-neutral experiment records.

The command is intentionally local and dependency-free. It records usage and
cost metadata supplied by an adapter or operator; it does not call a model or
AWS. This keeps experiment accounting usable for local models, hosted
non-AWS models, and AWS-backed runs alike.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROVIDERS = ("local", "aws", "openai", "anthropic", "google", "other")
STATUSES = ("planned", "running", "success", "failed", "blocked")


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def money(value: float | None) -> float:
    return round(float(value or 0), 8)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def findings_template(name: str, run_id: str) -> str:
    return f"""# Findings: {name}

Run ID: `{run_id}`

## Question and hypothesis

- Question:
- Hypothesis:

## Setup

- Provider/runtime:
- Model/version:
- Region or local host:
- Input fixture:
- Prompt/configuration:

## Result

- Outcome:
- What worked:
- What failed or surprised us:
- Reproducibility notes:

## Trade-offs

### Advantages

-

### Limitations and risks

-

### Cost and latency interpretation

-

## Evidence

- Artifact:
- Trace/log:
- Usage/cost snapshot:

## Decision

- Keep, change, or reject:
- Next experiment:
"""


def init_run(args: argparse.Namespace) -> int:
    run_id = (
        args.run_id or f"{args.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    )
    run_dir = args.output_dir / run_id
    if run_dir.exists():
        raise ValueError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "experiment": {
            "name": args.name,
            "description": args.description or "",
            "status": "planned",
        },
        "execution": {
            "provider": args.provider,
            "mode": args.mode,
            "model": args.model or "",
            "region": args.region or "",
            "request_id": "",
            "runtime_session_id": "",
        },
        "input": {"path": "", "sha256": ""},
        "output": {"path": "", "summary": ""},
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "latency_ms": None,
        },
        "pricing": {
            "currency": "USD",
            "input_per_1m_tokens": None,
            "output_per_1m_tokens": None,
            "source": "",
            "as_of": "",
        },
        "costs": {
            "token_estimate_usd": None,
            "aws_observed_usd": None,
            "aws_estimated_usd": None,
            "other_estimated_usd": None,
            "total_estimated_usd": None,
            "accounting_note": "Token cost and infrastructure cost are recorded separately to avoid hiding double counting.",
        },
        "evidence": [],
        "findings": {
            "pros": [],
            "cons": [],
            "limitations": [],
            "decision": "",
            "next_experiment": "",
        },
        "cleanup": {
            "required": args.provider == "aws",
            "status": "not_started",
            "notes": "",
        },
    }
    save_json(run_dir / "manifest.json", manifest)
    (run_dir / "findings.md").write_text(
        findings_template(args.name, run_id), encoding="utf-8"
    )
    print(run_dir)
    return 0


def optional_float(value: str | None) -> float | None:
    return None if value is None else money(value)


def usage_from_file(path: Path) -> dict[str, int]:
    value = load_json(path)
    value = value.get("usage", value)
    aliases = {
        "input_tokens": ("input_tokens", "prompt_tokens", "inputTokens"),
        "output_tokens": ("output_tokens", "completion_tokens", "outputTokens"),
        "total_tokens": ("total_tokens", "totalTokens"),
    }
    normalized: dict[str, int] = {}
    for target, keys in aliases.items():
        for key in keys:
            if value.get(key) is not None:
                normalized[target] = int(value[key])
                break
    return normalized


def record_run(args: argparse.Namespace) -> int:
    manifest_path = args.run_dir / "manifest.json"
    manifest = load_json(manifest_path)
    usage = manifest["usage"]
    pricing = manifest["pricing"]
    costs = manifest["costs"]

    file_usage = usage_from_file(args.usage_json) if args.usage_json else {}
    for key, value in {
        "input_tokens": args.input_tokens
        if args.input_tokens is not None
        else file_usage.get("input_tokens"),
        "output_tokens": args.output_tokens
        if args.output_tokens is not None
        else file_usage.get("output_tokens"),
        "total_tokens": args.total_tokens
        if args.total_tokens is not None
        else file_usage.get("total_tokens"),
        "latency_ms": args.latency_ms,
    }.items():
        if value is not None:
            usage[key] = value
    if (
        usage["total_tokens"] is None
        and usage["input_tokens"] is not None
        and usage["output_tokens"] is not None
    ):
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

    if args.input_rate is not None:
        pricing["input_per_1m_tokens"] = money(args.input_rate)
    if args.output_rate is not None:
        pricing["output_per_1m_tokens"] = money(args.output_rate)
    if args.pricing_source:
        pricing["source"] = args.pricing_source
    if args.pricing_as_of:
        pricing["as_of"] = args.pricing_as_of

    if (
        usage["input_tokens"] is not None
        and usage["output_tokens"] is not None
        and pricing["input_per_1m_tokens"] is not None
        and pricing["output_per_1m_tokens"] is not None
    ):
        costs["token_estimate_usd"] = money(
            usage["input_tokens"] * pricing["input_per_1m_tokens"] / 1_000_000
            + usage["output_tokens"] * pricing["output_per_1m_tokens"] / 1_000_000
        )

    if args.aws_observed is not None:
        costs["aws_observed_usd"] = money(args.aws_observed)
    if args.aws_estimated is not None:
        costs["aws_estimated_usd"] = money(args.aws_estimated)
    if args.other_estimated is not None:
        costs["other_estimated_usd"] = money(args.other_estimated)

    aws_cost = (
        costs["aws_observed_usd"]
        if costs["aws_observed_usd"] is not None
        else costs["aws_estimated_usd"]
    )
    known_costs = [costs["token_estimate_usd"], aws_cost, costs["other_estimated_usd"]]
    if any(value is not None for value in known_costs):
        costs["total_estimated_usd"] = money(sum(value or 0 for value in known_costs))

    execution = manifest["execution"]
    for key, value in {
        "request_id": args.request_id,
        "runtime_session_id": args.runtime_session_id,
    }.items():
        if value:
            execution[key] = value
    if args.status:
        manifest["experiment"]["status"] = args.status
    if args.output_path:
        manifest["output"]["path"] = args.output_path
    if args.output_summary:
        manifest["output"]["summary"] = args.output_summary
    if args.input_path:
        manifest["input"]["path"] = args.input_path
    if args.evidence:
        manifest["evidence"].append(
            {"path": args.evidence, "captured_at": utc_now(), "note": args.note or ""}
        )
    if args.note:
        manifest["findings"]["limitations"].append(args.note)
    manifest["updated_at"] = utc_now()
    save_json(manifest_path, manifest)
    return 0


def finalize_run(args: argparse.Namespace) -> int:
    manifest_path = args.run_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["experiment"]["status"] = args.status
    if args.decision:
        manifest["findings"]["decision"] = args.decision
    if args.next_experiment:
        manifest["findings"]["next_experiment"] = args.next_experiment
    if args.cleanup_status:
        manifest["cleanup"]["status"] = args.cleanup_status
    if args.cleanup_note:
        manifest["cleanup"]["notes"] = args.cleanup_note
    manifest["updated_at"] = utc_now()
    save_json(manifest_path, manifest)
    return 0


def check_run(args: argparse.Namespace) -> int:
    manifest = load_json(args.run_dir / "manifest.json")
    required = [
        "schema_version",
        "run_id",
        "created_at",
        "experiment",
        "execution",
        "usage",
        "pricing",
        "costs",
        "evidence",
        "findings",
        "cleanup",
    ]
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValueError(f"manifest missing required keys: {', '.join(missing)}")
    if manifest["execution"].get("provider") not in PROVIDERS:
        raise ValueError("execution.provider is not a supported provider category")
    if manifest["experiment"].get("status") not in STATUSES:
        raise ValueError("experiment.status is not supported")
    print(
        json.dumps(
            {
                "run_id": manifest["run_id"],
                "status": manifest["experiment"]["status"],
                "total_estimated_usd": manifest["costs"].get("total_estimated_usd"),
            },
            indent=2,
        )
    )
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a run directory and manifest")
    init.add_argument("--name", required=True)
    init.add_argument("--provider", choices=PROVIDERS, required=True)
    init.add_argument("--model")
    init.add_argument("--mode", default="single_request")
    init.add_argument("--region")
    init.add_argument("--description")
    init.add_argument("--run-id")
    init.add_argument("--output-dir", type=Path, default=Path("experiments/runs"))
    init.set_defaults(handler=init_run)

    record = commands.add_parser(
        "record", help="record usage, costs, evidence, or status"
    )
    record.add_argument("--run-dir", type=Path, required=True)
    record.add_argument("--status", choices=STATUSES)
    record.add_argument("--input-tokens", type=int)
    record.add_argument("--output-tokens", type=int)
    record.add_argument("--total-tokens", type=int)
    record.add_argument(
        "--usage-json", type=Path, help="provider response JSON containing usage fields"
    )
    record.add_argument("--latency-ms", type=int)
    record.add_argument("--input-rate", type=float, help="USD per 1M input tokens")
    record.add_argument("--output-rate", type=float, help="USD per 1M output tokens")
    record.add_argument("--pricing-source")
    record.add_argument("--pricing-as-of")
    record.add_argument(
        "--aws-observed", type=float, help="observed AWS spend from billing data"
    )
    record.add_argument(
        "--aws-estimated", type=float, help="estimated AWS spend before billing settles"
    )
    record.add_argument("--other-estimated", type=float)
    record.add_argument("--request-id")
    record.add_argument("--runtime-session-id")
    record.add_argument("--input-path")
    record.add_argument("--output-path")
    record.add_argument("--output-summary")
    record.add_argument("--evidence")
    record.add_argument("--note")
    record.set_defaults(handler=record_run)

    finalize = commands.add_parser(
        "finalize", help="set final result and cleanup state"
    )
    finalize.add_argument("--run-dir", type=Path, required=True)
    finalize.add_argument(
        "--status", choices=("success", "failed", "blocked"), required=True
    )
    finalize.add_argument("--decision")
    finalize.add_argument("--next-experiment")
    finalize.add_argument(
        "--cleanup-status",
        choices=("not_started", "complete", "partial", "not_required"),
    )
    finalize.add_argument("--cleanup-note")
    finalize.set_defaults(handler=finalize_run)

    check = commands.add_parser("check", help="validate the manifest shape")
    check.add_argument("--run-dir", type=Path, required=True)
    check.set_defaults(handler=check_run)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"experiment command failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

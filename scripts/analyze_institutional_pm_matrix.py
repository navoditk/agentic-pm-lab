"""Analyze repeated Institutional PM matrix runs and apply promotion gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from src.evaluation.matrix_analysis import apply_gates, summarize_runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/matrix.json",
    )
    parser.add_argument(
        "--gates", type=Path, default=ROOT / "config/evaluation-gates.yaml"
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/matrix-analysis.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "docs/learning/INSTITUTIONAL_PM_SCORECARD_V2.md",
    )
    args = parser.parse_args()
    matrix: dict[str, Any] = json.loads(args.matrix.read_text())
    gates = yaml.safe_load(args.gates.read_text())
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in matrix["runs"]:
        groups.setdefault(run["model"], []).append(run)
    analyses = []
    for model, runs in groups.items():
        summary = summarize_runs(runs)
        analyses.append(
            {"model": model, "summary": summary, "gates": apply_gates(summary, gates)}
        )
    observed_repetitions = max(
        (item["summary"]["run_count"] for item in analyses), default=0
    )
    minimum_repetitions = gates["minimum_repetitions_for_promotion"]
    repetition_message = (
        f"The matrix contains {observed_repetitions} observed repetition(s) per "
        f"model at most; the configured promotion threshold is "
        f"{minimum_repetitions}."
    )
    analysis = {
        "matrix_id": matrix["matrix_id"],
        "scenario_coverage": matrix["scenarios"],
        "models": analyses,
    }
    args.output_json.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Institutional PM Scorecard v2",
        "",
        "> This report extends the [baseline four-model comparison](CANONICAL_PM_BENCHMARK_REPORT.md) without replacing it.",
        f"> {repetition_message}",
        "",
        "## Repeated-run analysis",
        "",
        "| Model | Runs | Success rate | Mean score | Score stdev | Mean tokens | p95 latency | Cost/run | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in analyses:
        summary = item["summary"]
        lines.append(
            f"| `{item['model']}` | {summary['run_count']} | {summary['success_rate']:.1%} | {summary['automated_score']['mean']:.2f} | {summary['automated_score']['stdev']:.2f} | {summary['total_tokens']['mean']:.0f} | {summary['latency_ms']['p95']:.0f} ms | ${summary['cost_per_successful_run_usd'] or 0:.6f} | {item['gates']['status']} |"
        )
    lines += [
        "",
        "## Scenario coverage",
        "",
        "| Scenario | Status | Purpose |",
        "|---|---|---|",
    ]
    lines += [
        f"| `{item['scenario_id']}` | {item['status']} | {item['purpose']} |"
        for item in matrix["scenarios"]
    ]
    lines += [
        "",
        "## Promotion interpretation",
        "",
        f"{repetition_message} Adversarial scenarios remain planned until provider adapters execute them and append immutable run records.",
        "",
        "AWS cost/run is a token estimate using standard on-demand Bedrock rates; the temporary AgentCore runtime, logging, and storage components are recorded separately and are not included when their asynchronous cost lookup returns zero or unavailable.",
        "",
    ]
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines))
    print(f"wrote {args.output_md}")
    print(f"wrote {args.output_json}")


if __name__ == "__main__":
    main()

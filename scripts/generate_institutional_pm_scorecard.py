"""Generate the advanced deterministic Institutional PM evaluation scorecard."""

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


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render(scorecard: dict[str, Any]) -> str:
    lines = [
        "# Institutional PM Advanced Evaluation Scorecard",
        "",
        f"> Evaluation contract: `{scorecard['evaluation_id']}`. Baseline comparison: [`CANONICAL_PM_BENCHMARK_REPORT.md`](CANONICAL_PM_BENCHMARK_REPORT.md).",
        "> Automated checks are deterministic; qualitative narrative review remains explicitly pending.",
        "",
        "## Evaluation architecture",
        "",
        "See [`docs/architecture/DIAGRAMS.md`](../architecture/DIAGRAMS.md#8-advanced-benchmark-evaluation-and-evidence-flow) for the full request-to-score-to-evidence flow.",
        "",
        "## Automated cross-model scorecard",
        "",
        "| Provider | Model | Score | Status | Critical failure | Tokens | Latency | Cost | Qualitative review |",
        "|---|---|---:|---|---|---:|---:|---:|---|",
    ]
    for result in scorecard["results"]:
        metrics = result["metrics"]
        tokens = metrics.get("total_tokens") or "—"
        latency = metrics.get("latency_ms")
        latency_text = "—" if latency is None else f"{latency / 1000:.3f}s"
        cost = metrics.get("estimated_cost_usd")
        cost_text = "—" if cost is None else f"${cost:.6f}"
        qualitative = result.get("qualitative_review", {})
        qualitative_text = (
            f"{qualitative['overall_score']:.1f}/5"
            if qualitative.get("overall_score") is not None
            else "pending"
        )
        lines.append(
            f"| {result['provider']} | `{result['model']}` | {result['automated_score']:.2f}/100 | {result['status']} | {'yes' if result['critical_failure'] else 'no'} | {tokens} | {latency_text} | {cost_text} | {qualitative_text} |"
        )
    lines += [
        "",
        "## Dimension definitions",
        "",
        "| Dimension | Automated check |",
        "|---|---|",
        "| Business completeness | Required risks and committee recommendation present |",
        "| Numerical fidelity | Rates and credit scenario outputs match tolerance |",
        "| Evidence grounding | Claims carry evidence identifiers |",
        "| Risk coverage | Expected high/medium findings present |",
        "| Governance compliance | Human approval required, no order execution, evaluation passes |",
        "| Observability completeness | Response, usage, latency, session, audit, and workflow evidence linked |",
        "",
        "## Qualitative review",
        "",
        "These reviews are structured comparative assessments of the observed outputs. They are not independent investment advice or a calibrated committee consensus.",
        "",
        "| Model | Score | Strengths | Limitations |",
        "|---|---:|---|---|",
    ]
    for result in scorecard["results"]:
        qualitative = result.get("qualitative_review", {})
        if qualitative.get("overall_score") is not None:
            lines.append(
                f"| `{result['model']}` | {qualitative['overall_score']:.1f}/5 | {qualitative['strengths']} | {qualitative['limitations']} |"
            )
    lines += [
        "",
        "## Interpretation",
        "",
        "This is not a model leaderboard. A model with a higher score is not promotable if it has a critical governance failure. The scorecard deliberately reports the original four-model operational comparison separately, preserves every run artifact, and adds quality checks without overwriting baseline results.",
        "",
        "### Evidence links",
    ]
    for result in scorecard["results"]:
        lines.append(
            f"- `{result['model']}`: [`{result['run_id']}`](../../experiments/runs/{result['run_id']}/)"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/benchmark.json",
    )
    parser.add_argument(
        "--expected",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/expected_results.json",
    )
    parser.add_argument(
        "--qualitative",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/qualitative_reviews.json",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "experiments/canonical-pm-benchmark/scorecard.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "docs/learning/INSTITUTIONAL_PM_EVALUATION_SCORECARD.md",
    )
    args = parser.parse_args()
    expected = load(args.expected)
    qualitative = load(args.qualitative)
    benchmark = load(args.benchmark)
    results = []
    for provider in benchmark["providers"]:
        if provider.get("alignment") != "canonical_exact" or not provider.get("run_id"):
            continue
        run_dir = ROOT / "experiments/runs" / provider["run_id"]
        manifest = load(run_dir / "manifest.json")
        response = load(
            run_dir / "response.json"
            if (run_dir / "response.json").exists()
            else run_dir / "hosted-response.json"
        )
        result = evaluate_response(
            response, manifest, expected, evidence_file_names(run_dir)
        )
        review = qualitative.get("reviews", {}).get(provider["run_id"])
        if review:
            result["qualitative_review"] = {
                "status": "reviewed_not_calibrated",
                "review_id": qualitative["review_id"],
                "method": qualitative["method"],
                **review,
            }
        results.append(result)
    scorecard = {
        "evaluation_id": expected["evaluation_id"],
        "benchmark_id": benchmark["benchmark_id"],
        "results": results,
        "notes": [
            "Baseline four-model results remain in CANONICAL_PM_BENCHMARK_REPORT.md.",
            "Qualitative review is structured but not yet calibrated against independent human committee reviewers.",
        ],
    }
    args.output_json.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render(scorecard), encoding="utf-8")
    print(f"wrote {args.output_md}")
    print(f"wrote {args.output_json}")


if __name__ == "__main__":
    main()

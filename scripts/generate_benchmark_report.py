"""Generate the learner-facing canonical institutional PM benchmark report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.model_roles import DEFAULT_ROLES_PATH, load_roles, model_string


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.6f}".rstrip("0").rstrip(".")
    return str(value)


def ms_to_seconds(value: int | None) -> str:
    return "—" if value is None else f"{value / 1000:,.3f} s"


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render(benchmark: dict[str, Any], roles: dict[str, Any] | None = None) -> str:
    providers = benchmark["providers"]
    exact = [p for p in providers if p["alignment"] == "canonical_exact"]
    roles = roles or load_roles()
    conductor = roles["conductor"]
    report_default = roles["report_generation"]["default"]
    report_review = roles["report_generation"]["review"]
    lines = [
        f"# {benchmark['title']}",
        "",
        f"> Generated from `{benchmark['benchmark_id']}` version `{benchmark['version']}`.",
        "> This report distinguishes observed evidence from historical related runs and planned reruns.",
        "",
        "## Executive summary",
        "",
        benchmark["business_objective"],
        "",
        f"Canonical business question: **{benchmark['business_question']}**",
        "",
        f"Observed exact-capstone providers: **{len(exact)}**. The OpenAI and Ollama results are valuable historical learning runs, but are explicitly not treated as apples-to-apples results because they used different question sets.",
        "",
        "The strongest current observability evidence is the OpenAI Day 6 run, which combines OpenTelemetry, LangSmith, a golden dataset, and regression evaluators. The strongest exact business-workflow evidence is the AgentCore Claude run. Direct Anthropic now provides a non-AWS exact-capstone reference with native token accounting and audit evidence.",
        "",
        "## Execution model roles",
        "",
        f"- **Default conductor:** `{model_string(conductor)}` — {conductor['purpose']}",
        f"- **Default report generation:** `{model_string(report_default)}` — {report_default['purpose']}",
        f"- **Higher-quality report review:** `{model_string(report_review)}` — {report_review['purpose']}",
        "",
        "These roles are automation defaults, not benchmark targets. The conductor coordinates the run, validates evidence, and handles bounded recovery; deterministic gates—not the conductor—decide whether a run is complete. Report generation may use the cheaper default profile, while discrepancy review may use Sonnet. Credentials are runtime-only and the report never records them.",
        "",
        "## 1. Business workflow under test",
        "",
        "The workflow is a read-only morning investment-committee review. It combines deterministic investment analytics with model-assisted research synthesis and a Devil's Advocate challenge. The model may explain and prioritize evidence, but it cannot authorize itself or place an order.",
        "",
        "### Input contract",
        "",
        f"- Identity: `{benchmark['input_contract']['identity']}`",
        f"- Portfolio: `{benchmark['input_contract']['portfolio_id']}`",
        f"- Decision date: `{benchmark['input_contract']['decision_date']}`",
        f"- Data policy: {benchmark['input_contract']['data_policy']}",
        "- Output boundary: evidence-linked review, human approval required, no order execution",
        "",
        "### Canonical workflow stages",
        "",
        "```text",
        " → ".join(benchmark["workflow_stages"]),
        "```",
        "",
        "The learner should inspect the stage trace, audit events, evidence IDs, policy decisions, token metrics, latency, and final approval state. Private model chain-of-thought is not captured; structured tool calls and governance artifacts are the supported traceability boundary.",
        "",
        "## 2. Reproducibility contract",
        "",
        "Every strict comparison must hold these values constant:",
        "",
        bullet_lines(
            [
                "business question, identity, portfolio ID, and decision date",
                "point-in-time data snapshot and research bundle",
                "tool contracts, authorization policies, guardrail cases, and prompt version",
                "workflow stage names and output schema",
                "evaluation dataset and scoring thresholds",
                "experiment manifest, trace ID, and evidence retention policy",
            ]
        ),
        "",
        "Two modes are required:",
        "",
        f"- **Controlled synthesis:** {benchmark['benchmark_modes'][0]['purpose']}",
        f"- **Full agentic:** {benchmark['benchmark_modes'][1]['purpose']}",
        "",
        "## 3. Consolidated observed results",
        "",
        "| Provider | Model | Surface | Alignment | Tokens (in/out/total) | Latency | Est. cost | Observability | Governance |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for p in providers:
        tokens = "/".join(
            fmt(p[key]) for key in ("input_tokens", "output_tokens", "total_tokens")
        )
        cost = (
            "—"
            if p.get("estimated_cost_usd") is None
            else f"${p['estimated_cost_usd']:.6f}"
        )
        obs = ", ".join(p["observability"])
        lines.append(
            f"| {p['provider']} | `{p['model']}` | {p['surface']} | {p['alignment']} | {tokens} | {ms_to_seconds(p.get('latency_ms'))} | {cost} | {obs} | {p['governance']} |"
        )
    lines += [
        "",
        "### Cost interpretation",
        "",
        "Direct Anthropic and OpenAI values are token-based estimates using the rates captured for those runs. AWS values are account/day Cost Explorer estimates and must not be interpreted as the price of one model request. Local Ollama is recorded as zero model-service cost, excluding electricity and hardware opportunity cost.",
        "",
        "## 4. Exact-capstone comparison",
        "",
        "The following providers used the canonical capstone input and can be compared directly for the observed run-level metrics:",
        "",
        "| Provider/model | Tokens | Latency | Cost basis | Approval | Order execution |",
        "|---|---:|---:|---|---|---|",
    ]
    for p in exact:
        tokens = "/".join(
            fmt(p[key]) for key in ("input_tokens", "output_tokens", "total_tokens")
        )
        cost = (
            "—"
            if p.get("estimated_cost_usd") is None
            else f"${p['estimated_cost_usd']:.6f}"
        )
        basis = p.get("cost_basis", "provider token estimate")
        lines.append(
            f"| `{p['model']}` | {tokens} | {ms_to_seconds(p.get('latency_ms'))} | {basis}; {cost} | yes | no |"
        )
    lines += [
        "",
        "This table is not a quality leaderboard. Token count and latency depend on prompt shape, runtime overhead, output ceilings, and provider instrumentation. Quality requires the common evaluator suite and human review of evidence grounding.",
        "",
        "## 5. Observability and traceability model",
        "",
        "```text",
        "Canonical request",
        "    │ trace_id / experiment_id / snapshot_hash",
        "    ├── OTel root span: pm.capstone",
        "    │     ├── authz + policy decision",
        "    │     ├── data/provenance spans",
        "    │     ├── tool/delegation spans",
        "    │     ├── guardrail + approval spans",
        "    │     └── token / latency / cost attributes",
        "    ├── LangSmith: agent trace, dataset, evaluator results",
        "    ├── CloudWatch/AgentCore: hosted runtime logs and metrics",
        "    └── Experiment manifest: normalized result, findings, evidence links",
        "```",
        "",
        "Required span attributes include provider, model, prompt version, tool contract version, input/output tokens, latency, cost basis, data snapshot hash, evidence IDs, policy result, guardrail result, retry status, approval state, and order-execution state. Do not log secrets or private chain-of-thought.",
        "",
        "## 6. Evaluation scorecard",
        "",
        "| Dimension | What the evaluator should verify |",
        "|---|---|",
    ]
    for dimension in benchmark["evaluation_dimensions"]:
        lines.append(
            f"| {dimension.title()} | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |"
        )
    lines += [
        "",
        "The Day 6 OpenAI baseline provides the current deepest evaluation implementation: routing/retrieval context, tool selection/arguments, final-answer criteria, token/cost/latency, OTel, LangSmith, and regression gates. The exact-capstone runs currently provide workflow and governance evidence but need to be replayed through this full scorecard for a complete cross-provider quality matrix.",
        "",
        "## 7. Learner walkthrough",
        "",
        "1. Read the [direct model run guide](../guides/DIRECT_MODEL_RUNS.md) and [experiments README](../../experiments/README.md).",
        "2. Run the offline fixture and inspect its stage trace and audit JSONL.",
        "3. Inspect the exact-capstone manifests linked below; separate model tokens from AWS account/day costs.",
        "4. Open the OpenAI observability/evaluation notes to understand LangSmith and OTel depth.",
        "5. Compare evidence coverage before comparing model quality.",
        "6. Rerun missing providers only with the same canonical input and record a new manifest; never overwrite historical evidence.",
        "",
        "### Evidence links",
        "",
        "- [OpenAI OTel/LangSmith baseline](../learning/observability-evaluation.md#baseline-runs)",
        "- [Direct Anthropic run](../../experiments/runs/anthropic-direct-capstone-20260816-230000/)",
        "- [AWS Claude exact canonical rerun](../../experiments/runs/canonical-claude-20260817-022944-34585c43/)",
        "- [AWS Llama exact canonical rerun](../../experiments/runs/canonical-llama-20260817-024235-eb81a0d4/)",
        "- [Historical model comparison](../learning/comparison-notes.md)",
        "",
        "## 8. Current gaps and next benchmark actions",
        "",
        bullet_lines(benchmark["known_gaps"]),
        "",
        "The benchmark is therefore **partially observed**, not a completed quality ranking. The next promotion criterion is a five-provider exact-input replay in both modes, with the same evaluator suite and trace schema, followed by a generated comparison report and human review of evidence grounding.",
        "",
        "## Report provenance",
        "",
        "This report is generated by `scripts/generate_benchmark_report.py` from `experiments/canonical-pm-benchmark/benchmark.json`. Historical values are reproduced from the linked experiment manifests and learning records; no unrecorded model calls are inferred.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("experiments/canonical-pm-benchmark/benchmark.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/learning/CANONICAL_PM_BENCHMARK_REPORT.md"),
    )
    parser.add_argument("--roles-config", type=Path, default=DEFAULT_ROLES_PATH)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render(load(args.input), load_roles(args.roles_config)), encoding="utf-8"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

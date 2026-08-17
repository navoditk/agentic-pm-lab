"""Run the institutional PM capstone through OpenAI's Responses API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.capstone.workflow import run_institutional_pm_capstone
from src.observability.telemetry import observe_agent_run

DEFAULT_MODEL = "gpt-4.1-mini"
INPUT_RATE_PER_MILLION = 0.40
OUTPUT_RATE_PER_MILLION = 1.60


def _stage(stages: list[dict[str, Any]], name: str, **details: Any) -> None:
    stages.append({"stage": name, "details": details})


def run_capstone(
    *,
    question: str,
    identity: str,
    portfolio_id: str,
    decision_date: str,
    audit_log: Path,
    model: str = DEFAULT_MODEL,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run deterministic controls/calculations, then direct OpenAI narration."""
    request_id = request_id or f"openai-capstone-{uuid.uuid4().hex}"
    stages: list[dict[str, Any]] = []
    _stage(stages, "request_received", request_id=request_id)
    _stage(stages, "input_validated", identity=identity, portfolio_id=portfolio_id)
    _stage(
        stages,
        "authorization_checked",
        decision="delegated_to_local_cedar_boundary",
    )
    capstone = run_institutional_pm_capstone(
        identity=identity,
        portfolio_id=portfolio_id,
        decision_date=decision_date,
        audit_log_path=audit_log,
    )
    _stage(stages, "capstone_completed", workflow=capstone["workflow"])
    prompt = (
        "You are a read-only institutional PM reviewer. Summarize the supplied "
        "deterministic capstone result for a human committee. State evidence, "
        "risks, uncertainty, and the next review step. Do not reveal private "
        "chain-of-thought.\n\n"
        f"Question: {question}\n"
        f"Evaluation: {json.dumps(capstone['evaluation'], sort_keys=True)}\n"
        f"Challenge findings: {json.dumps(capstone['committee_artifact']['challenge'], sort_keys=True)}\n"
        f"Workflow stages: {json.dumps(capstone['workflow'], sort_keys=True)}"
    )
    _stage(stages, "orchestration_started", tools=[], order_execution=False)
    started = time.perf_counter()
    with observe_agent_run("agent.openai.capstone.invoke", model) as (
        _span,
        metrics,
    ):
        response = OpenAI().responses.create(
            model=model,
            instructions="You provide concise, evidence-linked committee summaries.",
            input=prompt,
            max_output_tokens=300,
            temperature=0,
            store=False,
        )
        usage = response.usage
        metrics.input_tokens = int(usage.input_tokens)
        metrics.output_tokens = int(usage.output_tokens)
    usage_dict = {
        "input_tokens": int(response.usage.input_tokens),
        "output_tokens": int(response.usage.output_tokens),
        "total_tokens": int(response.usage.total_tokens),
    }
    _stage(stages, "openai_completed", usage=usage_dict)
    _stage(
        stages, "guardrail_checked", decision="local_capstone_boundary", violations=[]
    )
    _stage(stages, "response_emitted", approval_required=True, order_execution=False)
    return {
        "request_id": request_id,
        "provider": "openai",
        "model_id": model,
        "answer": response.output_text,
        "usage": usage_dict,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "response_id": response.id,
        "status": response.status,
        "capstone": capstone,
        "approval_required": True,
        "order_execution": False,
        "workflow_stages": stages,
        "pricing": {
            "currency": "USD",
            "input_per_million_tokens": INPUT_RATE_PER_MILLION,
            "output_per_million_tokens": OUTPUT_RATE_PER_MILLION,
            "estimated_token_cost_usd": round(
                (
                    usage_dict["input_tokens"] * INPUT_RATE_PER_MILLION
                    + usage_dict["output_tokens"] * OUTPUT_RATE_PER_MILLION
                )
                / 1_000_000,
                8,
            ),
            "basis": "OpenAI direct API standard token estimate; verify against provider billing.",
        },
        "reasoning_note": "Observable deterministic stages and governance outcomes are returned; private model chain-of-thought is not logged.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--identity", default="PM_USER")
    parser.add_argument("--portfolio-id", default="PORT_A")
    parser.add_argument("--decision-date", default="2026-08-13")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--request-id")
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY must be set; it is never read from a file.")
    result = run_capstone(
        question=args.question,
        identity=args.identity,
        portfolio_id=args.portfolio_id,
        decision_date=args.decision_date,
        audit_log=args.audit_log,
        model=args.model,
        request_id=args.request_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

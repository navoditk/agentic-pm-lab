"""Run the provider-neutral Day 21 Canvas PM workflow.

The default fixture mode executes the real local institutional capstone and
adds an operator-friendly execution and token-cost envelope. Provider modes are
validated here and fail closed until their explicit adapters are configured;
they must never silently fall back to fixture evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.capstone.workflow import run_institutional_pm_capstone

SUPPORTED_MODES = ("fixture", "local", "openai", "anthropic", "aws")
QUESTION_TO_PROMPT = {
    "risk_snapshot": "What are the largest current portfolio risks?",
    "rates_stress": "What happens if rates rise by 50 bps?",
    "portfolio_access": "Can I inspect PORT_B from this session?",
}


def estimate_tokens(text: str) -> int:
    """Use a transparent approximation when a provider gives no usage data."""
    return max(1, (len(text) + 3) // 4)


def request_id_for(question: str, mode: str) -> str:
    digest = hashlib.sha256(f"{mode}:{question}".encode()).hexdigest()[:16]
    return f"canvas-pm-{digest}"


def run_workflow(
    *,
    question: str,
    identity: str,
    portfolio_id: str,
    decision_date: str,
    mode: str,
    audit_log: Path,
) -> dict[str, Any]:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"mode must be one of {', '.join(SUPPORTED_MODES)}")
    request_id = request_id_for(question, mode)
    started = time.perf_counter()

    if mode != "fixture":
        return {
            "status": "blocked",
            "request_id": request_id,
            "mode": mode,
            "question": question,
            "provider_configured": False,
            "reason": (
                f"The {mode} adapter is intentionally not selected by the default "
                "Canvas exercise. Configure and evidence this provider separately; "
                "no fixture result was substituted."
            ),
            "next_step": {
                "local": "Configure Ollama and run the documented local Deep Agent comparison.",
                "openai": "Set OPENAI_API_KEY and run the hosted-model experiment path.",
                "anthropic": "Configure an approved Anthropic adapter and record its model/cost evidence.",
                "aws": "Use docs/AWS_AGENTCORE_SETUP.md and a budgeted AgentCore invocation.",
            }[mode],
            "execution_trace": [
                {
                    "stage": "provider_gate",
                    "component": "provider-neutral-runner",
                    "status": "blocked",
                    "mode": mode,
                }
            ],
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "cost": {"currency": "USD", "estimated_usd": 0.0, "basis": "not invoked"},
            "private_chain_of_thought_captured": False,
        }

    result = run_institutional_pm_capstone(
        identity=identity,
        portfolio_id=portfolio_id,
        decision_date=decision_date,
        audit_log_path=audit_log,
    )
    serialized_input = json.dumps(
        {"question": question, "identity": identity, "portfolio_id": portfolio_id},
        sort_keys=True,
    )
    serialized_output = json.dumps(result, sort_keys=True, default=str)
    input_tokens = estimate_tokens(serialized_input)
    output_tokens = estimate_tokens(serialized_output)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    audit_events = []
    if audit_log.exists():
        audit_events = [
            json.loads(line)
            for line in audit_log.read_text().splitlines()
            if line.strip()
        ]
    result.update(
        {
            "status": "completed",
            "request_id": request_id,
            "question": question,
            "mode": "fixture",
            "provider": "deterministic-local-capstone",
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "basis": "transparent character-count approximation; no model invoked",
            },
            "cost": {
                "currency": "USD",
                "estimated_usd": 0.0,
                "basis": "deterministic fixture run; no model invocation",
            },
            "latency_ms": elapsed_ms,
            "audit_events": audit_events,
            "private_chain_of_thought_captured": False,
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--identity", default="PM_USER")
    parser.add_argument("--portfolio-id", default="PORT_A")
    parser.add_argument("--decision-date", default="2026-08-13")
    parser.add_argument("--mode", choices=SUPPORTED_MODES, default="fixture")
    parser.add_argument("--audit-log", type=Path, required=True)
    args = parser.parse_args()
    args.audit_log.parent.mkdir(parents=True, exist_ok=True)
    output = run_workflow(
        question=args.question,
        identity=args.identity,
        portfolio_id=args.portfolio_id,
        decision_date=args.decision_date,
        mode=args.mode,
        audit_log=args.audit_log,
    )
    print(json.dumps(output, sort_keys=True, default=str))


if __name__ == "__main__":
    main()

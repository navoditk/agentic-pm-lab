"""Live lab: the Agent foundations loop with a real Bedrock model.

The offline Bedrock course runs this exact loop through botocore's Stubber.
This lab sends the same requests to Amazon Bedrock, so you can see a real
model ask for a tool, your code run it, and the answer come back.

    uv run python -m src.live_labs.bedrock_converse          # dry run
    uv run python -m src.live_labs.bedrock_converse --live   # one real run

Cost: at most three Converse calls, each capped at 300 output tokens. Input
is not capped; allowing a generous 2,000 input tokens per call, the worst case
at the rates in `MODEL_PRICES_PER_MILLION_USD` is about one US cent. The dry
run prints that bound, and a live run prints its actual tokens and cost. Credentials: an AWS identity allowed
`bedrock:InvokeModel` on the inference profile and on its foundation model
in each Region the profile routes to, with model access enabled. Cleanup:
none; nothing is created in AWS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-west-2"
MAX_STEPS = 3
MAX_TOKENS = 300
QUESTION = "What is the 3-year yield? Use the interpolation tool."


def _prices(model_id: str) -> dict[str, float] | None:
    from src.observability.telemetry import MODEL_PRICES_PER_MILLION_USD

    for name, rates in MODEL_PRICES_PER_MILLION_USD.items():
        if name in model_id:
            return rates
    return None


def worst_case_usd(model_id: str, *, input_tokens_per_call: int = 2000) -> float | None:
    """An upper bound: every call at the input estimate and the output cap."""
    rates = _prices(model_id)
    if rates is None:
        return None
    return (
        MAX_STEPS
        * (input_tokens_per_call * rates["input"] + MAX_TOKENS * rates["output"])
        / 1_000_000
    )


def first_request(model_id: str) -> dict[str, Any]:
    """The first Converse request the lab would send, built offline."""
    from src.foundations.agent_loop import demo_tools
    from src.runtime.bedrock_lab import ConverseModel

    model = ConverseModel(client=None, model_id=model_id, max_tokens=MAX_TOKENS)
    allowed = [t.spec() for t in demo_tools() if t.name == "interpolate_yield"]
    return model.request([{"role": "user", "content": QUESTION}], allowed)


def dry_run(model_id: str, region: str) -> None:
    bound = worst_case_usd(model_id)
    print("Dry run: nothing is sent to AWS.\n")
    print(f"Model:  {model_id}\nRegion: {region}")
    print(f"Limits: {MAX_STEPS} model calls, {MAX_TOKENS} output tokens each")
    if bound is not None:
        print(f"Worst case at the repository's recorded rates: ${bound:.4f}")
    print("\nFirst Converse request:")
    print(json.dumps(first_request(model_id), indent=2))
    print(
        "\nNeeds bedrock:InvokeModel on the inference profile and on its "
        "foundation model in each Region it routes to\n"
        "(see invoke_through_profile_policy in src/runtime/bedrock_lab.py). "
        "Run with --live to send it."
    )


def live_run(model_id: str, region: str) -> int:
    import boto3

    from src.foundations.agent_loop import demo_tools, run_agent
    from src.runtime.bedrock_lab import ConverseModel, total_input_tokens

    account = boto3.client("sts", region_name=region).get_caller_identity()["Account"]
    print(f"Calling Bedrock in {region} as account {account}.")
    model = ConverseModel(
        boto3.client("bedrock-runtime", region_name=region),
        model_id,
        max_tokens=MAX_TOKENS,
    )
    with tempfile.TemporaryDirectory() as scratch:
        result = run_agent(
            QUESTION,
            model,
            demo_tools(),
            allowed_tools={"interpolate_yield"},
            audit_log=Path(scratch) / "audit.jsonl",
            max_steps=MAX_STEPS,
        )
    usage = [r.get("usage", {}) for r in model.responses]
    tokens_in = sum(total_input_tokens(u) for u in usage)
    tokens_out = sum(u.get("outputTokens", 0) for u in usage)
    print(f"\nStop reason: {result.stop_reason}")
    print(f"Tools requested: {result.tool_calls_requested}")
    print(f"Audit: {[(r['tool_name'], r['decision']) for r in result.audit]}")
    print(f"Answer: {result.answer}")
    print(f"Trace id: {result.trace_id}")
    print(
        f"\n{len(usage)} model calls, {tokens_in} input and {tokens_out} output tokens."
    )
    rates = _prices(model_id)
    if rates:
        cost = (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1_000_000
        print(f"Cost at the repository's recorded rates: ${cost:.5f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--live", action="store_true", help="send real requests")
    parser.add_argument("--model", default=os.getenv("BEDROCK_LIVE_LAB_MODEL", MODEL))
    parser.add_argument("--region", default=os.getenv("AWS_REGION", REGION))
    args = parser.parse_args(argv)
    if not args.live:
        dry_run(args.model, args.region)
        return 0
    if os.getenv("CI"):
        print("Live labs never run in CI.", file=sys.stderr)
        return 2
    return live_run(args.model, args.region)


if __name__ == "__main__":
    raise SystemExit(main())

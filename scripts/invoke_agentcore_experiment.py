"""Invoke an AgentCore Runtime with a bounded JSON request.

This is an operational probe, not a unit-test helper. It uses the caller's
normal AWS profile and prints the response body so the request can be archived
alongside CloudWatch evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def invoke(
    runtime_arn: str, payload: dict, region: str, profile: str, endpoint: str
) -> bytes:
    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client("bedrock-agentcore")
    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        qualifier=endpoint,
        contentType="application/json",
        accept="application/json",
        runtimeSessionId=f"session-{uuid.uuid4().hex}",
        payload=json.dumps(payload).encode("utf-8"),
    )
    body = response.get("response")
    if body is None:
        raise RuntimeError(
            f"AgentCore response did not contain a response body: {response}"
        )
    return body.read() if hasattr(body, "read") else bytes(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-arn", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--profile", default="agentic-pm-lab")
    parser.add_argument("--endpoint", default="default")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = invoke(
            args.runtime_arn, payload, args.region, args.profile, args.endpoint
        )
        if args.output:
            args.output.write_bytes(result)
        else:
            sys.stdout.buffer.write(result)
            sys.stdout.buffer.write(b"\n")
        return 0
    except (OSError, ValueError, BotoCoreError, ClientError, RuntimeError) as error:
        print(f"AgentCore invocation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

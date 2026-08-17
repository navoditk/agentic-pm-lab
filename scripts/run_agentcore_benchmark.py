"""Run exact-input AgentCore benchmark models with evidence and cleanup.

The package is built separately because AgentCore Runtime requires a Linux
ARM64 artifact. This script owns the cloud lifecycle after the package exists:
upload, runtime/endpoint creation, invocation, evidence capture, normalized
experiment recording, and finally cleanup of only the run's resources.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "experiments/agentcore-runtime-proof/input.json"
DEFAULT_MODELS = {
    "claude": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "llama": "us.meta.llama3-3-70b-instruct-v1:0",
}


@dataclass
class RunResources:
    run_id: str
    run_dir: Path
    run_prefix: str
    runtime_id: str = ""
    runtime_arn: str = ""
    endpoint_created: bool = False


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, default=str, indent=2, sort_keys=True) + "\n")


def invoke_record_command(args: list[str]) -> None:
    subprocess.run(
        [sys.executable, "scripts/experiment.py", *args],
        cwd=REPO_ROOT,
        check=True,
    )


def init_run(run_id: str, model: str, region: str) -> RunResources:
    run_dir = REPO_ROOT / "experiments/runs" / run_id
    invoke_record_command(
        [
            "init",
            "--name",
            f"Canonical PM benchmark {model}",
            "--provider",
            "aws",
            "--mode",
            "temporary_agentcore_runtime",
            "--model",
            model,
            "--region",
            region,
            "--run-id",
            run_id,
        ]
    )
    return RunResources(run_id, run_dir, run_id)


def wait_for_status(
    getter: Any,
    *,
    attempts: int = 30,
    delay_seconds: int = 10,
) -> str:
    last_status = ""
    for attempt in range(1, attempts + 1):
        last_status = str(getter())
        print(f"AgentCore status poll {attempt}/{attempts}: {last_status}", flush=True)
        if last_status == "READY":
            return last_status
        if "FAILED" in last_status:
            raise RuntimeError(
                f"AgentCore resource entered failure state: {last_status}"
            )
        time.sleep(delay_seconds)
    raise TimeoutError(f"AgentCore resource did not become READY: {last_status}")


def invoke_runtime(
    data_client: Any,
    runtime_arn: str,
    payload: dict[str, Any],
    *,
    attempts: int = 3,
    retry_delay_seconds: int = 15,
) -> tuple[bytes, str, float]:
    """Invoke a warm endpoint, retrying only the documented cold-start timeout."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        session_id = f"canonical-{uuid.uuid4().hex}"
        started = time.perf_counter()
        try:
            response = data_client.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                qualifier="default",
                contentType="application/json",
                accept="application/json",
                runtimeSessionId=session_id,
                payload=json.dumps(payload).encode("utf-8"),
            )
            body = response["response"]
            try:
                raw_response = body.read() if hasattr(body, "read") else bytes(body)
            finally:
                if hasattr(body, "close"):
                    body.close()
            latency_ms = round((time.perf_counter() - started) * 1000, 3)
            return raw_response, session_id, latency_ms
        except (BotoCoreError, ClientError, RuntimeError) as error:
            last_error = error
            if (
                "initialization time exceeded" not in str(error).lower()
                or attempt == attempts - 1
            ):
                raise
            time.sleep(retry_delay_seconds)
    raise RuntimeError(f"AgentCore invocation failed after retries: {last_error}")


def wait_for_endpoint_deletion(
    getter: Any,
    *,
    attempts: int = 30,
    delay_seconds: int = 5,
) -> None:
    """Wait until asynchronous endpoint deletion is visible to the control plane."""
    for attempt in range(1, attempts + 1):
        try:
            getter()
        except (ClientError, BotoCoreError) as error:
            if "notfound" in str(error).replace(" ", "").lower():
                return
            raise
        print(
            f"AgentCore endpoint deletion poll {attempt}/{attempts}: still present",
            flush=True,
        )
        time.sleep(delay_seconds)
    raise TimeoutError("AgentCore endpoint did not finish deleting")


def capture_log_evidence(
    logs_client: Any,
    resources: RunResources,
    region: str,
) -> None:
    log_group = f"/aws/bedrock-agentcore/runtimes/{resources.runtime_id}-default"
    try:
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
        )
        write_json(resources.run_dir / "log-streams.json", streams)
        events = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=int((time.time() - 3600) * 1000),
        )
        write_json(resources.run_dir / "events.json", events)
    except logs_client.exceptions.ResourceNotFoundException as error:
        write_json(
            resources.run_dir / "logs-unavailable.json",
            {"region": region, "log_group": log_group, "error": str(error)},
        )


def capture_cost_evidence(ce_client: Any, resources: RunResources) -> float | None:
    start = datetime.now(UTC).date()
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": (start + timedelta(days=1)).isoformat(),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    write_json(resources.run_dir / "cost.json", response)
    results = response.get("ResultsByTime", [])
    if not results:
        return None
    amount = results[0].get("Total", {}).get("UnblendedCost", {}).get("Amount")
    return None if amount is None else float(amount)


def cleanup(
    control_client: Any,
    s3_client: Any,
    logs_client: Any,
    resources: RunResources,
    bucket: str,
    region: str,
) -> list[str]:
    errors: list[str] = []
    if resources.endpoint_created:
        try:
            control_client.delete_agent_runtime_endpoint(
                agentRuntimeId=resources.runtime_id,
                endpointName="default",
            )
            wait_for_endpoint_deletion(
                lambda: control_client.get_agent_runtime_endpoint(
                    agentRuntimeId=resources.runtime_id,
                    endpointName="default",
                )
            )
        except (ClientError, BotoCoreError) as error:
            if "notfound" not in str(error).replace(" ", "").lower():
                errors.append(f"endpoint cleanup: {error}")
        except TimeoutError as error:
            errors.append(f"endpoint cleanup: {error}")
    if resources.runtime_id:
        try:
            control_client.delete_agent_runtime(
                agentRuntimeId=resources.runtime_id,
            )
        except (ClientError, BotoCoreError) as error:
            errors.append(f"runtime cleanup: {error}")
    try:
        s3_client.delete_object(
            Bucket=bucket, Key=f"{resources.run_prefix}/runtime.zip"
        )
    except (ClientError, BotoCoreError) as error:
        errors.append(f"S3 cleanup: {error}")
    for suffix in ("default", "DEFAULT"):
        try:
            logs_client.delete_log_group(
                logGroupName=f"/aws/bedrock-agentcore/runtimes/{resources.runtime_id}-{suffix}"
            )
        except logs_client.exceptions.ResourceNotFoundException:
            pass
        except (ClientError, BotoCoreError) as error:
            errors.append(f"log cleanup ({suffix}): {error}")
    return errors


def run_one(
    *,
    session: boto3.Session,
    model_label: str,
    model_id: str,
    package_path: Path,
    input_path: Path,
    bucket: str,
    role_arn: str,
    region: str,
    max_attempts: int,
    invoke_attempts: int,
) -> dict[str, Any]:
    run_id = f"canonical-{model_label}-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    resources = init_run(run_id, model_id, region)
    control = session.client("bedrock-agentcore-control")
    data = session.client("bedrock-agentcore")
    s3 = session.client("s3")
    logs = session.client("logs")
    budgets = session.client("budgets")
    ce = session.client("ce")
    cleanup_errors: list[str] = []
    success = False
    try:
        s3.upload_file(
            str(package_path),
            bucket,
            f"{resources.run_prefix}/runtime.zip",
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        write_json(
            resources.run_dir / "s3-upload.json",
            {"bucket": bucket, "key": f"{resources.run_prefix}/runtime.zip"},
        )
        artifact = {
            "codeConfiguration": {
                "code": {
                    "s3": {
                        "bucket": bucket,
                        "prefix": f"{resources.run_prefix}/runtime.zip",
                    }
                },
                "runtime": "PYTHON_3_13",
                "entryPoint": ["agentcore_app.py"],
            }
        }
        create = control.create_agent_runtime(
            agentRuntimeName=f"canonical_pm_{model_label}_{uuid.uuid4().hex[:8]}",
            description=f"Canonical PM benchmark {model_label}",
            roleArn=role_arn,
            agentRuntimeArtifact=artifact,
            networkConfiguration={"networkMode": "PUBLIC"},
            protocolConfiguration={"serverProtocol": "HTTP"},
            lifecycleConfiguration={
                "idleRuntimeSessionTimeout": 900,
                "maxLifetime": 3600,
            },
            environmentVariables={"MODEL_ID": model_id},
            clientToken=run_id,
        )
        resources.runtime_id = create["agentRuntimeId"]
        resources.runtime_arn = create["agentRuntimeArn"]
        write_json(resources.run_dir / "runtime-create.json", create)
        wait_for_status(
            lambda: control.get_agent_runtime(agentRuntimeId=resources.runtime_id)[
                "status"
            ],
            attempts=max_attempts,
        )
        write_json(
            resources.run_dir / "runtime.json",
            control.get_agent_runtime(agentRuntimeId=resources.runtime_id),
        )
        endpoint = control.create_agent_runtime_endpoint(
            agentRuntimeId=resources.runtime_id,
            name="default",
            agentRuntimeVersion="1",
        )
        resources.endpoint_created = True
        write_json(resources.run_dir / "endpoint-create.json", endpoint)
        wait_for_status(
            lambda: control.get_agent_runtime_endpoint(
                agentRuntimeId=resources.runtime_id,
                endpointName="default",
            )["status"],
            attempts=max_attempts,
        )
        write_json(
            resources.run_dir / "endpoint.json",
            control.get_agent_runtime_endpoint(
                agentRuntimeId=resources.runtime_id,
                endpointName="default",
            ),
        )
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        raw_response, session_id, latency_ms = invoke_runtime(
            data,
            resources.runtime_arn,
            payload,
            attempts=invoke_attempts,
        )
        response_path = resources.run_dir / "hosted-response.json"
        response_path.write_bytes(raw_response)
        captured = json.loads(raw_response)
        captured["benchmark_metadata"] = {
            "model_label": model_label,
            "model_id": model_id,
            "runtime_session_id": session_id,
            "latency_ms": latency_ms,
        }
        write_json(response_path, captured)
        capture_log_evidence(logs, resources, region)
        try:
            write_json(
                resources.run_dir / "budget.json",
                budgets.describe_budget(
                    AccountId=session.client("sts").get_caller_identity()["Account"],
                    BudgetName="agentic-pm-lab-monthly",
                ),
            )
        except (ClientError, BotoCoreError) as error:
            write_json(
                resources.run_dir / "budget-unavailable.json", {"error": str(error)}
            )
        try:
            aws_cost = capture_cost_evidence(ce, resources)
        except (ClientError, BotoCoreError) as error:
            aws_cost = None
            write_json(
                resources.run_dir / "cost-unavailable.json", {"error": str(error)}
            )
        record_args = [
            "record",
            "--run-dir",
            str(resources.run_dir),
            "--status",
            "success",
            "--usage-json",
            str(response_path),
            "--latency-ms",
            str(round(latency_ms)),
            "--request-id",
            str(captured.get("request_id", "")),
            "--runtime-session-id",
            session_id,
            "--input-path",
            "input.json",
            "--output-path",
            "hosted-response.json",
            "--evidence",
            "hosted-response.json,runtime.json,endpoint.json,events.json,log-streams.json,budget.json,cost.json",
            "--note",
            "Canonical exact-input full PM capstone; temporary AgentCore resources captured before cleanup.",
        ]
        if aws_cost is not None:
            record_args.extend(["--aws-estimated", str(aws_cost)])
        invoke_record_command(record_args)
        success = True
        return {"run_id": run_id, "status": "success", "response": captured}
    except (
        BotoCoreError,
        ClientError,
        OSError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as error:
        write_json(resources.run_dir / "failure.json", {"error": str(error)})
        return {"run_id": run_id, "status": "blocked", "error": str(error)}
    finally:
        cleanup_errors = cleanup(control, s3, logs, resources, bucket, region)
        final_status = "success" if success and not cleanup_errors else "blocked"
        decision = (
            f"Observed exact-input {model_label} run; human approval remains required and no order was executed."
            if success
            else "No usable model result was recorded."
        )
        if cleanup_errors:
            decision += " Cleanup errors were recorded."
        finalize_args = [
            "finalize",
            "--run-dir",
            str(resources.run_dir),
            "--status",
            final_status,
            "--decision",
            decision,
            "--next-experiment",
            "Run the common evaluator suite against the canonical benchmark output.",
            "--cleanup-status",
            "partial" if cleanup_errors else "complete",
            "--cleanup-note",
            "; ".join(cleanup_errors)
            if cleanup_errors
            else "Runtime, endpoint, unique S3 prefix, and log groups deleted.",
        ]
        invoke_record_command(finalize_args)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--profile", default="agentic-pm-lab")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--bucket")
    parser.add_argument("--role-arn")
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--max-attempts", type=int, default=30)
    parser.add_argument("--invoke-attempts", type=int, default=3)
    args = parser.parse_args()
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    account_id = session.client("sts").get_caller_identity()["Account"]
    bucket = args.bucket or f"bedrock-agentcore-code-{account_id}-{args.region}"
    role_arn = (
        args.role_arn
        or f"arn:aws:iam::{account_id}:role/AgenticPMLabRuntimeExecutionRole"
    )
    model_specs = args.model or [
        f"{key}={value}" for key, value in DEFAULT_MODELS.items()
    ]
    results = []
    for specification in model_specs:
        label, separator, model_id = specification.partition("=")
        if not separator or not label or not model_id:
            raise ValueError(f"--model must be label=model-id, got {specification!r}")
        results.append(
            run_one(
                session=session,
                model_label=label,
                model_id=model_id,
                package_path=args.package,
                input_path=args.input,
                bucket=bucket,
                role_arn=role_arn,
                region=args.region,
                max_attempts=args.max_attempts,
                invoke_attempts=args.invoke_attempts,
            )
        )
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if all(result["status"] == "success" for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())

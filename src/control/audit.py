"""Append-only JSON Lines audit log for tool-call authorization decisions.

Every Cedar authorization decision at the Tool Layer boundary should also log
here, so a denied or approved call is always reconstructable after the fact
— this becomes load-bearing once Day 7 wires it against real Cedar decisions.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from opentelemetry import trace

from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_LOG_PATH = REPO_ROOT / "data" / "cache" / "audit.jsonl"
AuditDecision = Literal["allowed", "denied", "interrupted"]
AuditLayer = Literal["AuthN", "AuthZ", "Guardrail", "Tool"]


def current_trace_id() -> str | None:
    """Return the active OTel trace ID, if this call is currently traced."""
    context = trace.get_current_span().get_span_context()
    return f"{context.trace_id:032x}" if context.is_valid else None


def record_audit_event(
    identity: str,
    role: str,
    tool_name: str,
    decision: AuditDecision,
    layer: AuditLayer,
    *,
    resource_id: str | None = None,
    log_path: Path = DEFAULT_AUDIT_LOG_PATH,
) -> dict:
    """Append one audit record and return it."""
    with observe_operation(
        "control.record_audit_event",
        "audit",
        {
            "app.auth.role": role,
            "app.auth.tool": tool_name,
            "app.auth.decision": decision,
            "app.auth.layer": layer,
        },
    ):
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "identity": identity,
            "role": role,
            "tool_name": tool_name,
            "resource_id": resource_id,
            "decision": decision,
            "layer": layer,
            "trace_id": current_trace_id(),
        }
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record


def read_audit_log(log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> list[dict]:
    """Read all audit records currently in the log, oldest first."""
    if not log_path.exists():
        return []
    with log_path.open() as f:
        return [json.loads(line) for line in f if line.strip()]

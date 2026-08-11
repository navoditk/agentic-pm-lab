"""Append-only JSON Lines audit log for tool-call authorization decisions.

Every check_permission() call at the Tool Layer boundary should also log
here, so a denied or approved call is always reconstructable after the fact
— this becomes load-bearing once Day 7 wires it against real Cedar decisions.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_LOG_PATH = REPO_ROOT / "data" / "cache" / "audit.jsonl"


def record_audit_event(
    identity: str,
    role: str,
    tool_name: str,
    allowed: bool,
    log_path: Path = DEFAULT_AUDIT_LOG_PATH,
) -> dict:
    """Append one audit record and return it."""
    with observe_operation(
        "control.record_audit_event",
        "audit",
        {
            "app.auth.role": role,
            "app.auth.tool": tool_name,
            "app.auth.allowed": allowed,
        },
    ):
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "identity": identity,
            "role": role,
            "tool_name": tool_name,
            "allowed": allowed,
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

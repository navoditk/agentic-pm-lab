"""Cedar-backed tool and portfolio authorization decisions."""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from cedarpy import Decision, PolicySet, is_authorized

from src.control.identity import role_for_identity
from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICIES_DIR = REPO_ROOT / "governance" / "policies"


def _load_policy(name: str) -> PolicySet:
    return PolicySet.from_str((POLICIES_DIR / name).read_text())


TOOL_POLICY = _load_policy("tool-permissions.cedar")
PORTFOLIO_POLICY = _load_policy("portfolio-access.cedar")


class NamedTool(Protocol):
    name: str


def check_tool_permission(role: str, tool_name: str) -> bool:
    """Return the Cedar decision for a role invoking one tool."""
    result = is_authorized(
        {
            "principal": {"type": "Role", "id": role},
            "action": {"type": "Action", "id": "invoke"},
            "resource": {"type": "Tool", "id": tool_name},
            "context": {},
        },
        TOOL_POLICY,
        [],
    )
    allowed = result.decision == Decision.Allow
    with observe_operation(
        "control.check_tool_permission",
        "authorization",
        {
            "app.auth.role": role,
            "app.auth.tool": tool_name,
            "app.auth.allowed": allowed,
        },
    ):
        return allowed


def check_portfolio_access(identity: str, portfolio_id: str) -> bool:
    """Return the Cedar decision for an identity accessing one portfolio."""
    result = is_authorized(
        {
            "principal": {"type": "User", "id": identity},
            "action": {"type": "Action", "id": "access"},
            "resource": {"type": "Portfolio", "id": portfolio_id},
            "context": {},
        },
        PORTFOLIO_POLICY,
        [],
    )
    allowed = result.decision == Decision.Allow
    with observe_operation(
        "control.check_portfolio_access",
        "authorization",
        {
            "app.auth.identity": identity,
            "app.auth.portfolio_id": portfolio_id,
            "app.auth.allowed": allowed,
        },
    ):
        return allowed


def tools_for_identity[ToolType: NamedTool](
    identity: str,
    tools: Sequence[ToolType],
) -> tuple[ToolType, ...]:
    """Filter tools before model binding using the identity's Cedar role."""
    role = role_for_identity(identity)
    if role is None:
        raise ValueError(f"Unknown identity: {identity}")
    return tuple(
        candidate for candidate in tools if check_tool_permission(role, candidate.name)
    )

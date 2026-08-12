import pytest

from src.control.authorization import (
    check_portfolio_access,
    check_tool_permission,
)
from src.control.identity import role_for_identity


@pytest.mark.parametrize(
    ("identity", "allowed_tool", "denied_tool"),
    [
        ("PM_USER", "price-bond", "delete_portfolio"),
        ("RISK_USER", "risk", "price-bond"),
        ("ADMIN_USER", "research", "delete_portfolio"),
    ],
)
def test_tool_permission_has_allowed_and_denied_paths(
    identity,
    allowed_tool,
    denied_tool,
):
    role = role_for_identity(identity)

    assert role is not None
    assert check_tool_permission(role, allowed_tool)
    assert not check_tool_permission(role, denied_tool)


@pytest.mark.parametrize(
    ("identity", "allowed_portfolio", "denied_portfolio"),
    [
        ("PM_USER", "PORT_A", "PORT_B"),
        ("RISK_USER", "PORT_B", "PORT_UNKNOWN"),
        ("ADMIN_USER", "PORT_B", "PORT_UNKNOWN"),
    ],
)
def test_portfolio_permission_has_allowed_and_denied_paths(
    identity,
    allowed_portfolio,
    denied_portfolio,
):
    assert check_portfolio_access(identity, allowed_portfolio)
    assert not check_portfolio_access(identity, denied_portfolio)

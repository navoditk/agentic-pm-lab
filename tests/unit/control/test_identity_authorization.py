from src.control.authorization import check_portfolio_access, check_tool_permission
from src.control.identity import IDENTITIES, role_for_identity


def test_pm_role_can_call_all_current_tools():
    for tool in (
        "price-bond",
        "curve",
        "research",
        "econometrics",
        "backtest",
        "portfolio",
        "risk",
    ):
        assert check_tool_permission("pm", tool)


def test_risk_role_cannot_call_price_bond():
    assert not check_tool_permission("risk", "price-bond")


def test_risk_role_can_call_portfolio():
    assert check_tool_permission("risk", "portfolio")


def test_risk_role_can_call_risk_metrics():
    assert check_tool_permission("risk", "risk")


def test_unknown_role_has_no_permissions():
    assert not check_tool_permission("nonexistent_role", "curve")


def test_unknown_tool_is_never_permitted():
    assert not check_tool_permission("admin", "delete_everything")


def test_role_for_identity_resolves_known_identities():
    assert role_for_identity("PM_USER") == "pm"
    assert role_for_identity("RISK_USER") == "risk"
    assert role_for_identity("ADMIN_USER") == "admin"


def test_role_for_identity_returns_none_for_unknown_identity():
    assert role_for_identity("nobody") is None


def test_roles_config_defines_exactly_the_three_day7_identities():
    assert IDENTITIES == {
        "PM_USER": "pm",
        "RISK_USER": "risk",
        "ADMIN_USER": "admin",
    }


def test_portfolio_policy_distinguishes_owned_and_cross_portfolio_access():
    assert check_portfolio_access("PM_USER", "PORT_A")
    assert not check_portfolio_access("PM_USER", "PORT_B")
    assert check_portfolio_access("RISK_USER", "PORT_A")
    assert check_portfolio_access("RISK_USER", "PORT_B")
    assert check_portfolio_access("ADMIN_USER", "PORT_B")

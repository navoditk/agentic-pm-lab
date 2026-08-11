from src.control.allowlist import ROLES, check_permission, role_for_identity


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
        assert check_permission("pm", tool)


def test_risk_role_cannot_call_price_bond():
    assert not check_permission("risk", "price-bond")


def test_risk_role_can_call_portfolio():
    assert check_permission("risk", "portfolio")


def test_risk_role_can_call_risk_metrics():
    assert check_permission("risk", "risk")


def test_unknown_role_has_no_permissions():
    assert not check_permission("nonexistent_role", "curve")


def test_unknown_tool_is_never_permitted():
    assert not check_permission("admin", "delete_everything")


def test_role_for_identity_resolves_known_identities():
    assert role_for_identity("pm_user") == "pm"
    assert role_for_identity("risk_user") == "risk"
    assert role_for_identity("admin_user") == "admin"


def test_role_for_identity_returns_none_for_unknown_identity():
    assert role_for_identity("nobody") is None


def test_roles_config_defines_exactly_the_three_day7_roles():
    assert set(ROLES.keys()) == {"pm", "risk", "admin"}

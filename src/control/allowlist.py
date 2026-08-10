"""# MOCK — replace on Day 7 with governance/policies/tool-permissions.cedar.

A hardcoded role->tool allowlist, loaded from config/roles.yaml (this
project's single source of truth for role permissions until Day 7 splits it).
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES_CONFIG_PATH = REPO_ROOT / "config" / "roles.yaml"


def _load_roles(config_path: Path = ROLES_CONFIG_PATH) -> dict:
    with config_path.open() as f:
        return yaml.safe_load(f)


_CONFIG = _load_roles()
ROLES: dict[str, list[str]] = {
    role: data["allowed_tools"] for role, data in _CONFIG["roles"].items()
}
IDENTITIES: dict[str, str] = _CONFIG["identities"]


def check_permission(role: str, tool_name: str) -> bool:
    """Return True if `role` is allowed to call `tool_name`."""
    return tool_name in ROLES.get(role, [])


def role_for_identity(identity: str) -> str | None:
    """Look up which role an identity has, per config/roles.yaml's identity->role mapping."""
    return IDENTITIES.get(identity)

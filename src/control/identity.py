"""Local test-identity resolution for the Day 7 control layer."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES_CONFIG_PATH = REPO_ROOT / "config" / "roles.yaml"


def _load_identities(config_path: Path = ROLES_CONFIG_PATH) -> dict[str, str]:
    with config_path.open() as file:
        config = yaml.safe_load(file)
    return dict(config["identities"])


IDENTITIES = _load_identities()


def role_for_identity(identity: str) -> str | None:
    """Resolve one local test identity to its assigned role."""
    role = IDENTITIES.get(identity)
    with observe_operation(
        "control.role_for_identity",
        "authentication",
        {
            "app.auth.identity": identity,
            "app.auth.identity_known": role is not None,
            "app.auth.role": role or "unknown",
        },
    ):
        return role


def identity_from_sources(sources: Mapping[str, Any]) -> str:
    """Read and validate the identity carried in named agent context."""
    user_role = sources.get("user_role")
    identity = user_role.get("identity") if isinstance(user_role, Mapping) else None
    if not isinstance(identity, str) or role_for_identity(identity) is None:
        raise ValueError("sources.user_role.identity must name a known identity")
    return identity

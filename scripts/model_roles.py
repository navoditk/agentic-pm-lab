"""Load the repository's provider-neutral automation model roles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROLES_PATH = REPO_ROOT / "config" / "model-roles.yaml"


def load_roles(path: Path = DEFAULT_ROLES_PATH) -> dict[str, Any]:
    """Load and minimally validate model-role configuration."""
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if value.get("schema_version") != 1:
        raise ValueError("model role configuration must use schema_version 1")
    for role in ("conductor", "report_generation"):
        if role not in value:
            raise ValueError(f"model role configuration missing {role}")
    return value


def model_string(role: dict[str, Any]) -> str:
    """Return a provider:model string suitable for Deep Agents."""
    return f"{role['provider']}:{role['model']}"

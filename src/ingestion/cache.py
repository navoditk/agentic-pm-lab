"""Small JSON-file cache shared by public data ingestors."""

import json
import time
from pathlib import Path
from typing import Any

DEFAULT_TTL_SECONDS = 24 * 60 * 60


def read_json_cache(
    path: Path,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    *,
    now: float | None = None,
) -> list[dict[str, Any]] | None:
    """Return cached records when the file is still within its TTL."""
    if ttl_seconds < 0:
        raise ValueError("ttl_seconds must be non-negative")
    if not path.exists():
        return None
    current_time = time.time() if now is None else now
    if current_time - path.stat().st_mtime > ttl_seconds:
        return None
    payload = json.loads(path.read_text())
    if not isinstance(payload, list) or not all(
        isinstance(record, dict) for record in payload
    ):
        raise ValueError(f"Cache file does not contain a record list: {path}")
    return payload


def write_json_cache(path: Path, records: list[dict[str, Any]]) -> None:
    """Atomically persist normalized records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(records, separators=(",", ":")))
    temporary_path.replace(path)

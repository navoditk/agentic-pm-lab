"""Check high-value documentation claims against repository state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def active_case_count() -> int:
    count = 0
    for path in sorted((ROOT / "evals").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip() and json.loads(line).get("status") != "stub":
                count += 1
    return count


def check() -> list[str]:
    errors: list[str] = []
    readme = (ROOT / "README.md").read_text()
    architecture = (ROOT / "docs/architecture/ARCHITECTURE.md").read_text()
    references = (ROOT / "docs/reference/REFERENCES.md").read_text()
    prd = (ROOT / "docs/architecture/PRD.md").read_text()
    if "175 passed" in readme:
        errors.append("README contains the retired 175-test claim")
    if "#the-layers-and-what-exists-today-day-20" in architecture:
        errors.append("architecture links to the retired Day 20 layer anchor")
    if "#logical-components-through-day-20" in architecture:
        errors.append("architecture links to the retired Day 20 component anchor")
    if "https://langchain-ai.github.io/langgraph/" in readme:
        errors.append("README uses the moved LangGraph documentation URL")
    if "https://opentelemetry.io/docs/specs/semconv/gen-ai/" in references:
        errors.append("references use the moved OpenTelemetry GenAI URL")
    actual_cases = active_case_count()
    if actual_cases != 22:
        errors.append(f"active evaluation case count is {actual_cases}, expected 22")
    if "22 active cases" not in architecture:
        errors.append("architecture does not state the current 22-case baseline")
    if "15 answer cases" not in prd:
        errors.append("PRD does not state the current 15-case golden boundary")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Documentation consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

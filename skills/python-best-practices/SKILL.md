---
name: python-best-practices
description: This project's Python coding conventions -- type hints, docstring format, the # MOCK marker convention, pytest naming/fixture patterns, and error-handling style for the Tool Layer. The most reused skill in the repo, since every day from here on writes Python.
license: MIT
covers:
  - .pre-commit-config.yaml
  - pyproject.toml
last_verified_commit: 909c2f2
---

# python-best-practices

Conventions any agent (or human) writing Python in this repo should follow. `ruff` and `pre-commit` enforce the mechanical parts of this automatically; the rest is judgment this skill exists to encode.

## Type hints

- Every function signature is fully typed — parameters and return type. Use built-in generics (`list[str]`, `dict[str, int]`, `str | None`) rather than `typing.List`/`Optional` — this project targets Python 3.12+.
- Prefer precise types over `Any`. If a dict's shape matters (e.g., an audit record), consider a `TypedDict` or a Pydantic model once the shape stabilizes rather than leaving it as `dict`.

## Docstrings

- Module-level docstring: one short paragraph explaining the module's purpose and, if applicable, what it mocks and when it's replaced.
- Function-level docstrings are one line unless the function's behavior genuinely needs more — this project follows the "no comments unless the why is non-obvious" principle from its own working conventions, and that extends to docstrings: a well-named function with typed arguments rarely needs a paragraph.

## The `# MOCK` marker convention

Every unfinished endpoint or function that stands in for real logic carries a docstring starting with `# MOCK — replace on Day N` (or, if permanently mocked by design, `# MOCK — stays mocked; <reason>`, e.g., the research tool per PRD.md §6). This is not just documentation — `scripts/check_progress.py` (§6) greps `src/` for this exact marker to derive `PROGRESS.md`'s mock→real status table. Removing the marker is literally what flips a row from mock to real; it is the mechanism, not a side note. Never leave a stale `# MOCK` marker on code that's actually been made real, and never remove one before the real implementation is actually in place.

## pytest conventions

- Test files: `tests/unit/<layer>/test_<module>.py`, mirroring `src/`'s structure (PLAN.md §4).
- Test functions: `test_<behavior_being_verified>`, not `test_<function_name>` — name the test after what it proves, not what it calls.
- Fixtures for shared setup (fixture role configs, fixture DuckDB connections, fixture test identities) live in `conftest.py` at the narrowest scope that needs them — a fixture used by only one test file's tests belongs in that directory, not the repo-wide `tests/conftest.py`.
- No test under `tests/unit/` may hit a real network call, API, or cloud resource — mock external dependencies (`responses`, `unittest.mock`, or recorded fixtures). This is a hard rule, not a preference (AGENTS.md repo rules).

## Error-handling style for the Tool Layer

- A Tool Layer function (`src/analytics/*`, `src/api/*`) raises a specific, typed exception for a caller-fixable problem (bad input, missing data) rather than returning `None` or a bare error string — callers need to be able to distinguish "this input was invalid" from "this succeeded with an empty result."
- Don't catch an exception you can't meaningfully handle at that layer — let it propagate to the FastAPI boundary, where a single exception handler translates it into the right HTTP status code, rather than scattering `try/except` blocks that just re-raise or log-and-swallow.
- Never validate for a scenario that structurally can't happen given the caller (e.g., don't re-check a role's permission inside an analytics function that's only ever called after the Control Layer boundary already checked it) — validate at the boundary, trust internal calls.

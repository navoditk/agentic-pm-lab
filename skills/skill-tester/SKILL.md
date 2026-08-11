---
name: skill-tester
description: Run local schema, static-contract, mock-execution, and behavioral checks against one repository skill package.
license: MIT
covers:
  - scripts/validate_skill.py
last_verified_commit: 8518262
---

# skill-tester

Use this meta-skill after creating or changing a skill and before committing.

## Local validation stages

1. **Schema/lint:** run
   `uv run python scripts/validate_skill.py skills/<name>`.
2. **Static contract:** confirm frontmatter and contract `covers` match, every
   required field exists, and `allowed_tools` is no broader than the behavior.
3. **Mock execution:** run
   `uv run pytest skills/<name>/tests -q`; tests must not call a live network,
   cloud resource, or model.
4. **Behavioral:** check the happy-path example and the highest-value negative
   constraint encoded by the skill.

Report each stage separately and fail on the first invalid package. Do not
rewrite the skill during validation or turn a failure into a warning.

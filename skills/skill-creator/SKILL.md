---
name: skill-creator
description: Scaffold a complete repository skill package with synchronized frontmatter, contract, example, and tests.
license: MIT
covers:
  - skills
last_verified_commit: 8518262
---

# skill-creator

Use this meta-skill before creating a new domain or process skill.

## Scaffold checklist

1. Confirm the behavior is reusable background knowledge, not a one-off prompt
   or a selectable custom-agent persona.
2. Create `skills/<name>/SKILL.md` with `name`, `description`, `license`,
   `covers`, and `last_verified_commit` frontmatter.
3. Create `contract.yaml` with explicit inputs, allowed and forbidden tools,
   output schema, side effects, approval requirement, synchronized `covers`,
   and a semantic version.
4. Add `examples/happy_path.json` plus a negative example when authorization,
   safety, or malformed inputs are meaningful.
5. Add `tests/test_skill.py` for frontmatter/contract synchronization and the
   skill's most important behavioral constraint.
6. Run `uv run python scripts/validate_skill.py skills/<name>` and the skill's
   pytest directory before committing.

Never broaden `allowed_tools` beyond what the skill actually needs. A skill's
contract documents allowed behavior but is not an authorization control.

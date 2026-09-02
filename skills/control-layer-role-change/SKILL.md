---
name: control-layer-role-change
description: Change local identity assignments or Cedar permissions without creating a second authority or weakening denied paths.
license: MIT
covers:
  - config/roles.yaml
  - governance/policies
  - src/control
  - src/agents
last_verified_commit: faf45b9
---

# control-layer-role-change

Use this skill when adding an identity, changing an identity's role, or
changing access to a tool or portfolio.

## Checklist

1. Classify the change before editing:
   - Identity-to-role assignment: update `config/roles.yaml` only.
   - Role-to-tool permission: update
     `governance/policies/tool-permissions.cedar` only.
   - Identity-to-portfolio permission: update
     `governance/policies/portfolio-access.cedar` only.
2. Never put an `allowed_tools` list in `config/roles.yaml`; Cedar is the sole
   permission authority.
3. Keep policies default-deny. Enumerate every new tool or portfolio
   deliberately, including administrator access; do not add an unrestricted
   wildcard to make a test pass.
4. Confirm `src/control/identity.py` resolves the assignment and
   `src/control/authorization.py` evaluates the intended Cedar policy.
5. Update Deep Agent tool-list construction in `src/agents/` when a new tool
   surface is introduced. Tool visibility reduces exposure but does not replace
   the Tool Layer boundary re-check.
6. Add an allowed and denied case to
   `governance/tests/test_authorization.py`. For portfolio access, exercise the
   same tool against both an allowed and denied portfolio.
7. Add or update `tests/unit/agents/test_role_gating.py` so the bound tool names
   match the policy decision for every identity.
8. Run `uv run python scripts/check_cedar_policies.py`, then
   `uv run pytest governance/tests tests/unit/control tests/unit/agents -q`.
9. Update the Security Model in `docs/architecture/ARCHITECTURE.md` when the effective
   identity, permission, approval, or trust-boundary model changes.

## Completion criteria

The identity assignment, Cedar decision, bound agent tools, Tool Layer
re-check, positive/negative tests, audit output, and Security Model must agree.
Never change `config/eval-baseline.json` to conceal an authorization failure.

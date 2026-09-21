# No-cost ways to make the platform more comprehensive

Moved out of `README.md`, where a roadmap sat between the curriculum and the
repository map and interrupted the reader's path. The content is unchanged;
only its location is.

None of these require live model or AWS spending, and each preserves the
repository's evidence boundary — they increase coverage and teaching value
without turning fixture output into a claim about production behaviour.

- Expand the golden dataset beyond its 22 active cases to cover every
  supported business question, with explicit `deferred` cases for
  unsupported ones.
- Add deterministic synthetic fixed-income fixtures for key-rate DV01,
  spread duration, carry/rolldown, benchmark-relative risk, liquidity, and
  mortgage-style negative convexity.
- Add walk-forward, look-ahead, stale-price, survivorship, corporate-action,
  slippage, and infeasible-constraint tests.
- Add synthetic multi-session Memory fixtures and local Gateway contract
  tests without deploying AWS resources.
- Add citation completeness, grounding, abstention, uncertainty, and
  contradiction evaluators over authored fixtures.
- Add local fault-injection scenarios for stale, unavailable, duplicated,
  conflicting, unlicensed, and prompt-injected evidence.
- Extend CI-enforced link validation beyond the generated curriculum
  artifact.
- Add a fully local browser/Canvas replay harness that checks state
  transitions and evidence presentation without claiming Copilot-hosted
  behaviour.

# Agent development lifecycle — deep dive

*Companion to [`.github/agents/agent-development-lifecycle-tutor.agent.md`](../../../.github/agents/agent-development-lifecycle-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py agent-development-lifecycle-tutor --quiz`.*

## What this actually is

Building an agentic system produces more than model prompts — it produces a
set of artifacts that describe what the agent is allowed to do, how it should
behave, and how another engineer (or another AI coding tool) can verify that
behavior without re-deriving it from scratch. That's the "agent development
lifecycle": skill packages that document reusable domain knowledge, prompt
files that package a repeatable workflow, custom agent personas that scope a
persistent role, and the tests/contracts that keep all three honest as the
underlying code changes.

The hard problem this discipline solves isn't writing the first version of an
artifact — it's *keeping it true*. A skill's documentation drifts from the
code it describes the moment someone changes the code and forgets the doc.
Most projects have no mechanism to catch that drift; this one does, and it's
worth understanding as a concrete instance of "documentation as a tested
artifact" rather than "documentation as a good intention."

## Core concepts

- **Skill.** Reusable background knowledge a model can draw on — not a
  one-off prompt, not a persona. Lives at `skills/<name>/` with a `SKILL.md`,
  a `contract.yaml`, `examples/`, and `tests/test_skill.py`.
- **Contract.** A machine-checkable description of a skill's or tool's
  boundaries: `inputs`, `allowed_tools`, `forbidden_tools`, `output_schema`,
  `side_effects`, `approval_required`. Crucially, a contract *documents*
  intent — it is not itself an enforcement mechanism (see Common pitfalls).
- **Prompt file.** A packaged, repeatable workflow (`.github/prompts/`),
  distinct from a skill (background knowledge) and a custom agent (a scoped
  persona).
- **Custom agent.** A `.github/agents/*.agent.md` file defining a persistent,
  scoped role — like the tutor personas this very document is a companion to.
- **Freshness.** The property that a skill's documentation still accurately
  describes the code it `covers`. Enforced mechanically, not by convention.
- **`covers`.** A list of repository paths in a skill's frontmatter (and
  mirrored in its `contract.yaml`) naming exactly which implementation files
  that skill is documenting. This is the join key the freshness check uses.
- **`last_verified_commit`.** The commit hash at which a human or agent last
  confirmed the skill's content matches its covered code. Not a timestamp of
  when the file was last edited — a claim about *verification*.

## How this repository implements it

`skills/skill-creator/SKILL.md` is the canonical scaffold recipe: create
`SKILL.md` with `name`/`description`/`license`/`covers`/`last_verified_commit`
frontmatter, a matching `contract.yaml`, an `examples/happy_path.json` (plus a
negative example when authorization/safety/malformed-input matters), and
`tests/test_skill.py` covering frontmatter-contract synchronization and the
skill's most important behavioral constraint. `skills/skill-tester/SKILL.md`
is the matching validation recipe — `scripts/validate_skill.py` runs
schema/lint checks, then a static contract check, then mock execution.

The enforcement mechanism is `scripts/check_skills_freshness.py`. Its
`audit_skills()` function takes a set of changed repository paths (from
`git diff --name-only`) and, for every `skills/*/SKILL.md`, checks whether any
changed path is `_covered()` by that skill's `covers` list. If a covered path
changed but the skill file itself isn't in the changed set, that's a stale
skill — the function returns an error string naming the skill and the
specific paths that triggered it. `main()` also passes
`require_existing_commit=True`, which separately verifies that
`last_verified_commit` actually names a real commit in this repository's
history (`git cat-file -e {commit}^{commit}`) — a check that catches typos and
copy-paste errors, not staleness itself.

`.github/workflows/skills-freshness.yml` runs this on every pull request,
diffing the PR's base and head SHAs. A PR that changes covered code without
touching the corresponding `SKILL.md` fails this check — unless it carries a
documented `skills-unaffected` label, the escape hatch for changes that
genuinely don't affect the skill's accuracy.

`skills/portfolio-optimization-narration/SKILL.md`
(`covers: [src/analytics/optimizer.py, contracts/tools/optimize_portfolio.schema.json]`)
paired with `.github/prompts/optimize-portfolio.prompt.md` is the concrete
example of a skill and a prompt file working together: the skill documents
how to narrate an optimization result, the prompt packages the repeatable
"run this workflow" invocation, and both are covered by the same freshness
gate whenever `optimizer.py` changes.

## Worked walkthrough

Trace what happens when someone changes `src/analytics/optimizer.py` without
touching its skill:

1. Read `skills/portfolio-optimization-narration/SKILL.md`'s frontmatter —
   note its `covers` list includes `src/analytics/optimizer.py`.
2. Read `audit_skills()` in `scripts/check_skills_freshness.py`: for each
   `skills/*/SKILL.md`, it computes `affected = sorted(path for path in
   changed if _covered(path, covers))`. If `affected` is non-empty and the
   skill's own path isn't in `changed`, it appends a stale-skill error.
3. Simulate it locally:
   ```bash
   uv run python scripts/check_skills_freshness.py --base HEAD~1 --head HEAD
   ```
   (Run this after a commit that touched `src/analytics/optimizer.py` alone,
   without the skill, to see the failure message; then run it again after
   including the skill file in the same diff range to see it pass.)
4. Read `tests/unit/scripts/test_check_skills_freshness.py` — it's a real
   regression test for this exact mechanism, not just documentation of intent.
5. Note what does *not* make the check pass: bumping `last_verified_commit`
   alone doesn't help, because `require_existing_commit=True` only checks that
   the referenced commit exists, not that the skill content is current —
   the actual fix is updating `covers` accuracy or the skill's content itself
   (or `git diff` shrinking so the covered path is no longer in `changed`,
   which isn't a real fix, just a coincidence).

## Common pitfalls

- **Treating `contract.yaml` as an authorization control.** A skill's
  `allowed_tools` list documents what the skill's author intended the skill
  to use — it is read by humans and by the freshness/contract-test tooling,
  never consulted by the actual runtime authorization path. Only
  `governance/policies/*.cedar` and the tool-boundary re-check in
  `src/api/main.py`/`src/mcp_server/server.py` decide what a live request can
  actually do. Widening `allowed_tools` changes nothing about real access.
- **Skipping `tests/test_skill.py` and hiding behavior in the prompt
  instead.** Untested, undocumented behavior that only lives in prompt text
  is invisible to the freshness check, invisible to `skill-tester`'s
  mock-execution stage, and invisible to the next engineer reading the skill
  package. If it matters, it belongs in the contract and a test, not just
  prose.
- **Confusing "file exists" with "file is current."** A skill's presence
  proves an artifact exists; only the freshness check (or a human diff
  review) proves it's still accurate. `last_verified_commit` existing in
  history is a much weaker claim than "the skill matches the code as of that
  commit," and the tooling is explicit about which of those two things it
  actually checks.

## Further reading

- [`docs/reference/REFERENCES.md#agent-harnesses-skills-prompts-and-custom-agents`](../reference/REFERENCES.md#agent-harnesses-skills-prompts-and-custom-agents)
- `docs/PLAN.md` §8 (skills/contracts/prompts/custom-agents catalog)
- `docs/guides/AGENT_RUNBOOK.md` for running a skill or custom agent standalone
- `tests/unit/scripts/test_check_skills_freshness.py` for the freshness
  mechanism's own regression coverage

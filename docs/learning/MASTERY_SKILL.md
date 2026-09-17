# Agentic PM Lab mastery skill

The **Agentic PM Lab Mastery** skill is the recommended conversational route
through the repository. It turns the existing 14 tutor courses into a guided
lesson, quiz, scenario, lab, teach-back, and cross-topic assessment flow across
GitHub Copilot, Claude Code, and Codex.

Learners without a local checkout can use the complete
[GitHub Pages curriculum](https://navoditk.github.io/agentic-pm-lab/) or the
repository's [standalone HTML artifact](../../artifacts/agentic-pm-curriculum.html).
Those routes include the deep dives, course outlines, labs, and browser-local
quizzes, but not CLI session progress or code-tracing exercises.

## Invoke it

Open this repository in GitHub Copilot CLI, Copilot coding agent, Claude Code,
or Codex, then say:

```text
agentexpert
```

You can also say `teach me FICC fundamentals`, `quiz me on governance`,
`give me a PM AI scenario`, `review my teach-back`, or `start the final
assessment`. The canonical, tool-neutral instruction package is
[`skills/agentic-pm-mastery/`](../../skills/agentic-pm-mastery/). Thin
tool-specific discovery loaders live at:

| CLI | Loader |
|---|---|
| GitHub Copilot | [`.github/skills/agentic-pm-mastery/`](../../.github/skills/agentic-pm-mastery/) |
| Claude Code | [`.claude/skills/agentic-pm-mastery/`](../../.claude/skills/agentic-pm-mastery/) |
| Codex | [`.agents/skills/agentic-pm-mastery/`](../../.agents/skills/agentic-pm-mastery/) |

The skill is read-only and offline by default. It uses local fixtures and
canonical repository sources; it does not call live providers, access
credentials, make investment recommendations, or execute trades.

## How the skill stays current

It reads `src/education/tutor.py` for the canonical topic catalog, then loads
the selected topic's course outline, deep dive, tutor persona, quiz bank, and
reference anchor on demand. Update those existing assets to change course
content; do not create a second topic registry in the skill.

Progress is session-only when the chosen CLI has no durable session store. For
a durable, CLI-neutral quiz record, use the companion CLI:

```bash
uv run python scripts/tutor.py <topic-id> --course
uv run python scripts/tutor.py <topic-id> --quiz
uv run python scripts/check_learner_progress.py
```

Use [TUTOR_COURSE_GUIDE.md](TUTOR_COURSE_GUIDE.md) for the completion rubric
and [DEPTH_PATH.md](DEPTH_PATH.md) for the orient, trace, break, teach method.
See [CURRICULUM_FRESHNESS_PLAN.md](CURRICULUM_FRESHNESS_PLAN.md) for the
external-documentation review roadmap.

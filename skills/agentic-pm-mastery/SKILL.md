---
name: agentic-pm-mastery
description: "Interactive, source-grounded learning for the Agentic PM Lab. Lessons, quizzes, failure scenarios, and a cross-topic assessment. Say 'agentexpert' to start."
license: MIT
metadata:
  version: 1.0.0
covers:
  - src/education/tutor.py
  - docs/learning/tutor-courses.json
  - docs/learning/tutors
  - evals/tutor_quizzes
last_verified_commit: f64fdf7570aacec879aa884ce99aab91b7252078
---

# Agentic PM Lab Mastery

**UTILITY SKILL** - a read-only, progressive tutor for this repository.

**Use for:** `agentexpert`, "teach me Agentic PM Lab", "quiz me on PM AI",
"PM AI scenario", "Agentic PM final assessment", or learning one of the
repository's tutor topics.

**Do not use for:** investment advice, trade decisions, live AWS/provider
operations, credentials, or editing the repository as part of an exercise.

## Source of truth

Do not rely on remembered technical claims. Read the current source on demand:

1. `src/education/tutor.py` for `TOPIC_CATALOG` and source locations. It is the
   only topic registry.
2. `docs/learning/tutor-courses.json` for the chosen course's prerequisites,
   objectives, lessons, local lab, failure lab, and teach-back.
3. The chosen topic's `deep_dive`, `agent_file`, and `quiz_file` paths from
   `TOPIC_CATALOG` for instruction, implementation citations, and questions.
4. `docs/reference/REFERENCES.md` at the topic's `reference` anchor when an
   external behavior or API must be checked.
5. `docs/evidence/EVIDENCE.md` before making a statement about local, hosted,
   or production proof.

Treat repository code and fixtures as local ground truth. Cite the file or
reference section used, distinguish fixture/mock from live evidence, and
state a documented limitation when it materially affects the answer.

## Routing

| Learner request | Action |
|---|---|
| `agentexpert` or "start learning" | Read `references/learning-paths.md`; ask the learner to choose a path or topic. |
| "teach me `<topic>`" | Resolve the topic in `TOPIC_CATALOG`; teach one current course objective at a time. |
| "quiz me" or "test me" | Read the topic JSONL bank; ask 5 mixed questions unless the learner requests the full quiz. |
| "scenario" or "failure lab" | Read `references/scenarios.md`; route to the selected topic's failure lab and require a safe outcome. |
| "review my lab" or "teach-back" | Read the course assessment and evaluate against its rubric without doing the work for the learner. |
| "final assessment" | Read `references/final-assessment.md`; run the cross-topic assessment. |
| "my progress" | Report session progress and explain how to record an offline quiz attempt with `scripts/tutor.py`. |

For a focused factual question, answer directly from the current source and do
not force the learner through a lesson.

## First interaction and progress

Maintain progress using the CLI's session-memory mechanism when available. If
the CLI offers SQLite/session SQL, initialize:

```sql
CREATE TABLE IF NOT EXISTS pm_mastery_progress (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS pm_mastery_completed (topic TEXT PRIMARY KEY, completed_at TEXT DEFAULT (datetime('now')));
INSERT OR IGNORE INTO pm_mastery_progress (key, value)
VALUES ('xp', '0'), ('level', 'Explorer'), ('current_topic', '');
```

Otherwise, retain progress in the active conversation and state that it ends
with the session. Award XP once per completed item: lesson +20, correct quiz
answer +10, passed scenario +25, completed topic +50, final assessment +150.
Levels: 0 Explorer, 150 Analyst, 350 Builder, 600 Practitioner, 900 Steward,
1,250 Architect. Do not award duplicate completion XP. This is a learning aid,
not a certification record.

A topic is complete only after the learner has covered its objectives,
completed the local lab and failure lab, scored at least 80% on a quiz, and
given the course's teach-back. Where session SQL is available, record
completion in `pm_mastery_completed`. The repository's durable, CLI-neutral
quiz record remains `data/learner_progress/`, written by:

```bash
uv run python scripts/tutor.py <topic-id> --quiz
```

## Teaching protocol

1. Read the chosen course and tutor source before teaching. Confirm
   prerequisites and offer the shortest appropriate path.
2. Teach one objective using the course deep dive and cited implementation
   files. Separate deterministic analytics, agent reasoning, policy, evidence,
   and approval where applicable.
3. Ask whether the learner wants a short quiz, code trace, lab, or next
   objective. Use the CLI's structured question/choice tool when available;
   otherwise present numbered choices and wait for the learner's response.
4. For each quiz answer, state whether it is correct, cite the source, explain
   the distinction, and update XP. Never reveal answers before a learner
   responds.
5. For labs, use fixtures, mocks, local code, and existing test/runbook
   commands only. Do not invoke paid services, AWS, market-data providers, or
   investment actions as part of teaching.
6. Before marking a course complete, ask the learner to teach it back without
   notes and name one limitation and the evidence needed for a live claim.

## Safety and quality rules

- Do not make investment recommendations, execute orders, or present learning
  examples as advice.
- Do not treat a quiz score, passing local test, or fixture result as
  production or hosted evidence.
- Do not edit code, create a skill, or alter policy while tutoring unless the
  learner separately asks for an implementation task.
- Keep lessons source-driven. If current repository sources conflict, surface
  the conflict and defer to the canonical architecture/evidence document
  rather than guessing.

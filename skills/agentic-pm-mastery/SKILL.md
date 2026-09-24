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
last_verified_commit: 13ae3f8c9563594031a8bea3dfa536d922bb75a6
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
2. `docs/learning/tutor-courses.json` for the chosen course's recommended
   `step`, `stage`, and `est_hours`, and its prerequisites, objectives,
   lessons, local lab, failure lab, and teach-back.
3. The chosen topic's `deep_dive`, `agent_file`, and `quiz_file` paths from
   `TOPIC_CATALOG` for instruction, implementation citations, and questions.
   `agent_file` is the CLI-neutral persona in `agents/`; the per-CLI copies
   under `.github/agents`, `.claude/agents`, and `.codex/agents` are generated
   from it, so read the source rather than a copy.
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
| `agentexpert` or "start learning" | Read `references/learning-paths.md`; ask the learner to choose a path or topic. On a first interaction, offer the placement quiz (`uv run agentic-pm-lab placement`, 12 concept questions, never recorded) to find which required courses they can skip ahead to the quiz. |
| "teach me `<topic>`" | Resolve the topic in `TOPIC_CATALOG`; teach one current course objective at a time. |
| "quiz me" or "test me" | Read the topic JSONL bank; ask 5 mixed questions as practice unless the learner requests the full quiz. With no topic named, run `uv run agentic-pm-lab review --list` and practise the concepts it lists, oldest miss first. Practice rounds are never recorded. |
| "record my quiz" or "full quiz" | Run a recorded quiz: see "Recording a quiz durably" below. |
| "scenario" or "failure lab" | Read `references/scenarios.md`; route to the selected topic's failure lab and require a safe outcome. |
| "build lab" or "let me build something" | Read the topic's `build_lab`; the learner writes the code. Review what they produce against whether it runs and whether its test would fail if the behaviour regressed — never write it for them. |
| "review my lab" or "teach-back" | Read the course assessment and evaluate against its rubric without doing the work for the learner. |
| "final assessment" | Read `references/final-assessment.md`; run the cross-topic assessment. |
| "my progress" | Report session progress, and tell the learner that `uv run agentic-pm-lab progress` shows every recorded quiz, from this conversation or the terminal, with a course-by-tier mastery matrix. |

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
with the session. Quiz results need not end with it: see "Recording a quiz
durably" below.

Award XP once per item, per topic. The caps keep every course worth the same,
so a level means the same thing whichever courses a learner took:

| Item | XP | Most per topic |
|---|---|---|
| Lesson taught | +20 each | 60 |
| Correct practice-quiz answer | +10, first 5 per topic | 50 |
| Failure lab or scenario passed | +25 | 25 |
| Build lab passed | +40 | 40 |
| Full quiz recorded that meets the pass rule | +50 | 50 |
| Topic complete | +50 | 50 |

A course is worth 275 XP, and all 18 courses plus the final assessment (+150)
is 5,100. The build lab is worth more than a scenario because it is the only
item that requires producing something that did not exist.

Levels: 0 Explorer, 275 Analyst, 1,925 Builder, 2,200 Integrator, 3,575 Practitioner, 5,100 Architect.

Each threshold is the XP for a milestone: the first course, then the XP of
the required Agent core module, then of Agent core plus the traceability
capstone (the whole required path), then of the next full module, then
every course and the final assessment. XP counts in any order, so a learner who skips the
optional Finance domain module reaches Practitioner through Platforms courses
instead. Do not award
duplicate XP. This is a learning aid, not a certification record.

A topic is complete only after the learner has covered its objectives,
completed the local lab, the failure lab and the build lab, passed a quiz
under the pass rule, and given the course's teach-back. The build lab is not
optional and cannot be substituted with a walkthrough: tracing, breaking and
explaining existing code all demonstrate comprehension, and only building
something that was not there demonstrates that you could do it again
unaided. Where session SQL is available, record
completion in `pm_mastery_completed`.

## Recording a quiz durably

The repository's durable, CLI-neutral quiz record is `data/learner_progress/`.
A learner can write to it from a terminal with
`uv run agentic-pm-lab quiz <topic-id>`, or from this conversation:

1. Only when the learner asks, ask **every** question in the topic's bank, in
   file order, one at a time. The recorder refuses a partial set, so a
   practice round cannot become a passed topic.
2. Collect the learner's own choice index for each question. Never fill in,
   correct, or infer an answer the learner did not give. Hold feedback until
   every answer is in, so the record reflects a closed-book attempt.
3. Run `uv run agentic-pm-lab quiz <topic-id> --answers <i1,i2,...>` with the
   indices in order, then go through the score and each missed question's
   citation.
4. That command appends one line to the gitignored
   `data/learner_progress/<topic-id>.jsonl` and changes nothing else. Do not
   regenerate or edit `docs/learning/LEARNER_PROGRESS.md`; tell the learner
   that `uv run agentic-pm-lab progress` updates it.

## Teaching protocol

1. Read the chosen course and tutor source before teaching. Confirm
   prerequisites and offer the shortest appropriate path.
2. Teach one objective using the course deep dive and cited implementation
   files. Separate deterministic analytics, agent reasoning, policy, evidence,
   and approval where applicable.
3. Ask whether the learner wants a short quiz, code trace, lab, or next
   objective. Use the CLI's structured question/choice tool when available;
   otherwise present numbered choices and wait for the learner's response.
4. For each quiz answer, state whether it is correct, cite the source, and
   explain the distinction, using the question's `explanation` when it has
   one. Show each question's `tier` (concept, implementation, or transfer)
   so the learner knows whether it tests the idea, this repository, or a new
   situation; a question with no `tier` is an implementation question. Update
   XP. Never reveal answers before a learner responds.
5. The pass rule is 80% overall **and** 70% within every tier the bank
   contains (`src/education/tutor.py::attempt_passes`), so say which tier
   fell short when a learner misses it. For practice on one tier, offer
   `uv run agentic-pm-lab quiz <topic-id> --tier <tier>`; practice is never
   recorded.
6. For labs, use fixtures, mocks, local code, and existing test/runbook
   commands only. Do not invoke paid services, AWS, market-data providers, or
   investment actions as part of teaching.
7. Before marking a course complete, ask the learner to teach it back without
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

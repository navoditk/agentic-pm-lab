# Start here

Every other document in this repository assumes you're the person who built
it, working through it day by day. This one doesn't. It's for someone opening
the repository for the first time, with no prior context, who wants to
understand what it is and actually learn from it — not just read about it.

Work through these steps in order. Each one is small; none require an AWS
account, a paid API key, or a specific IDE. Where a step needs something
optional, it says so.

1. **Read the pitch.** [`README.md`](../../README.md)'s "Purpose" and
   "Business problems and use cases" sections (the top third of the file) —
   skip everything below "Target technology stack" for now.
2. **Install and verify.** Follow [`INSTALL.md`](../../INSTALL.md) start to
   finish, including its verification checklist. Nothing below this line
   works without it.
3. **See what's already built.** Skim [`PROGRESS.md`](../../PROGRESS.md)'s
   generated status table — this tells you what exists today versus what's
   still roadmap, without you having to infer it from the code.
4. **List the tutors.** `uv run python scripts/tutor.py` — no arguments —
   prints all 14 domain tutor topics. This works in a plain terminal; it does
   not require Claude Code, Copilot, or Codex.
5. **Read one topic.** Pick whichever sounds most familiar and run
   `uv run python scripts/tutor.py <topic-id>` (e.g. `investment-data-tutor`).
   This prints that topic's scope, grounded in its own `.agent.md` file under
   `.github/agents/`.
6. **Take that topic's quiz.** `uv run python scripts/tutor.py <topic-id> --quiz`.
   It's 20-30 multiple-choice questions, graded immediately, each citing the
   real repository file that has the answer. Your result is logged locally.
7. **Check your own comprehension record.** Run
   `uv run python scripts/check_learner_progress.py`, then open
   [`docs/learning/LEARNER_PROGRESS.md`](LEARNER_PROGRESS.md). This is
   separate from `PROGRESS.md` — that file tracks whether code got built,
   this one tracks whether *you* understood it.
8. **Repeat steps 5–6 for two or three more topics** that sound relevant to
   what you want to learn. The [tutor catalog](../guides/TUTOR_RUNBOOK.md#tutor-catalog)
   maps each topic to the roadmap days it's most useful for, if you want a
   reason to pick one over another.
9. **Understand why it's built this way.** Read
   [`docs/architecture/PRD.md`](../architecture/PRD.md)'s business problems
   and non-goals, then [`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)'s
   layer table. This explains the separation between deterministic analytics
   and agent reasoning that every tutor keeps referring back to.
10. **Run the local stack.** Follow the "Quick start" section of
    [`docs/guides/RUNBOOK.md`](../guides/RUNBOOK.md) to bring up the API and
    run the test suite yourself. Seeing `175 passed` locally is more
    convincing than reading that number in a document.
11. **Try the optional UI.** `uv run streamlit run src/ui/app.py` gives you a
    browser-based version of steps 5–7 — a topic selector, the same scope
    text, and the same quiz, graded in place.
12. **See the governed end-to-end path (optional).** If you want to see the
    whole platform answer one realistic PM question, work through
    [`docs/guides/CANVAS_EXERCISES.md`](../guides/CANVAS_EXERCISES.md); it
    needs GitHub Copilot Canvas, so skip it if you don't have that available.
13. **Go deeper on one topic with an agent tool (optional).** If you have
    Claude Code, Copilot, or Codex available, open this repository in it and
    ask for one of the tutors by name — see
    [`docs/guides/TUTOR_RUNBOOK.md`](../guides/TUTOR_RUNBOOK.md#how-to-use-one-independently)
    for exact prompts. The CLI tutor in steps 4–7 is deliberately the same
    content, so this is a richer conversation over the same ground truth, not
    a different one.
14. **Decide where to go next.** If you're following the original 21-day
    build sequence, `AGENTS.md`'s day table and
    [`docs/learning/PHASE_1_RECAP.md`](PHASE_1_RECAP.md) pick up from here. If
    you just want to keep learning the finished platform, keep working
    through tutor topics and their quizzes (steps 4–8) until
    `LEARNER_PROGRESS.md` shows every topic passed.

Nothing above requires an AWS account, a paid model API key, or write access
to this repository — read the code, run the tests, take the quizzes.

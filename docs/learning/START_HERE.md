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
4. **Read the course instructions.** Open [`TUTOR_COURSE_GUIDE.md`](TUTOR_COURSE_GUIDE.md)
   to understand the complete sequence: prerequisites, lessons, labs, failure
   practice, quiz, and teach-back.
5. **List the tutors.** `uv run python scripts/tutor.py` — no arguments —
   prints all 14 domain tutor topics. This works in a plain terminal; it does
   not require Claude Code, Copilot, or Codex.
6. **Inspect one course.** Pick a topic and run
   `uv run python scripts/tutor.py <topic-id> --course`.
   This prints its objectives, lessons, labs, assessment, and repository paths.
7. **Read and trace the topic.** Run `uv run python scripts/tutor.py <topic-id>`
   for the tutor scope, read its linked deep dive and references, then trace
   the implementation and tests named by the course outline.
8. **Complete the labs before the quiz.** Run the local lab, then deliberately
   perform the failure lab and record the safe expected outcome. Both are
   fixture-based and require no paid services.
9. **Take that topic's quiz.** `uv run python scripts/tutor.py <topic-id> --quiz`.
   It is a 20–30 question multiple-choice assessment, graded immediately, with
   repository citations. Your result is logged locally.
7. **Check your own comprehension record.** Run
   `uv run python scripts/check_learner_progress.py`, then open
   [`docs/learning/LEARNER_PROGRESS.md`](LEARNER_PROGRESS.md). This is
   separate from `PROGRESS.md` — that file tracks whether code got built,
   this one tracks whether *you* understood it.
10. **Repeat steps 6–9 for two or three more topics** that sound relevant to
   what you want to learn. The [tutor catalog](../guides/TUTOR_RUNBOOK.md#tutor-catalog)
   maps each topic to the roadmap days it's most useful for, if you want a
   reason to pick one over another.
11. **Understand why it's built this way.** Read
   [`docs/architecture/PRD.md`](../architecture/PRD.md)'s business problems
   and non-goals, then [`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)'s
   layer table. This explains the separation between deterministic analytics
   and agent reasoning that every tutor keeps referring back to.
12. **Run the local stack.** Follow the "Quick start" section of
    [`docs/guides/RUNBOOK.md`](../guides/RUNBOOK.md) to bring up the API and
    run the test suite yourself. Seeing the current passing test count locally is more
    convincing than reading that number in a document.
13. **Try the optional UI.** `uv run streamlit run src/ui/app.py` gives you a
    browser-based version of steps 5–7 — a topic selector, the same scope
    text, and the same quiz, graded in place.
14. **See the governed end-to-end path (optional).** If you want to see the
    whole platform answer one realistic PM question, work through
    [`docs/guides/CANVAS_EXERCISES.md`](../guides/CANVAS_EXERCISES.md); it
    needs GitHub Copilot Canvas, so skip it if you don't have that available.
15. **Go deeper on one topic with an agent tool (optional).** If you have
    Claude Code, Copilot, or Codex available, open this repository in it and
    ask for one of the tutors by name — see
    [`docs/guides/TUTOR_RUNBOOK.md`](../guides/TUTOR_RUNBOOK.md#how-to-use-one-independently)
    for exact prompts. The CLI tutor in steps 4–7 is deliberately the same
    content, so this is a richer conversation over the same ground truth, not
    a different one.
16. **Go deep rather than stopping at orientation.** Follow the
    [topic depth path](DEPTH_PATH.md) for prerequisites, code tracing,
    adversarial exercises, and teach-backs. It uses fixtures and local tests;
    no paid model, AWS account, or live provider is required.
17. **Decide where to go next.** If you're following the original 21-day
    build sequence, `AGENTS.md`'s day table and
    [`docs/learning/PHASE_1_RECAP.md`](PHASE_1_RECAP.md) pick up from here. If
    you just want to keep learning the finished platform, keep working
    through tutor topics and their quizzes (steps 4–8) until
    `LEARNER_PROGRESS.md` shows every topic passed.

Nothing above requires an AWS account, a paid model API key, or write access
to this repository — read the code, run the tests, take the quizzes.

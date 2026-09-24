# Start here

This page is for someone opening the repository for the first time who wants
to learn from it, not rebuild it. Most other documents are written for the
person building the platform; you only need the ones linked below.

None of these routes needs an AWS account, a paid API key, or a specific IDE.

| Goal | Start here | What it provides |
|---|---|---|
| Browse without downloading | [GitHub Pages curriculum](https://navoditk.github.io/agentic-pm-lab/) or the [standalone HTML artifact](../../artifacts/agentic-pm-curriculum.html) | Every course, deep dive, and browser-local quiz; quizzes are learning checks, not durable completion. |
| Learn conversationally | Open a local checkout in Copilot, Claude Code, or Codex and say **`agentexpert`** | Guided lessons, scenarios, quizzes, and teach-back review from the [mastery skill](MASTERY_SKILL.md). |
| Complete evidence-backed courses | The seven steps below | Code tracing, runnable labs, failure practice, durable quiz records, and the completion rubric. |
| Build or contribute | [`INSTALL.md`](../../INSTALL.md), then [`AGENTS.md`](../../AGENTS.md) and [`PLAN.md`](../PLAN.md) | Rebuilding the platform day by day. Not needed for learning. |

## The local course path

1. **Get the code.** You need `git` and
   [`uv`](https://docs.astral.sh/uv/getting-started/installation/); `uv`
   installs the right Python for you.

   ```bash
   git clone https://github.com/navoditk/agentic-pm-lab.git
   cd agentic-pm-lab
   uv sync
   uv run agentic-pm-lab learn
   ```

   If the last command prints the course list, you are set up. Skip
   [`INSTALL.md`](../../INSTALL.md): it rebuilds the repository from an empty
   directory and sets up tools only the builder needs.

2. **Get the big picture (15 minutes).** Read the
   [README](../../README.md) through "The architecture in one view". The one
   idea every course comes back to: deterministic code does the math, the LLM
   reasons and narrates, and policy is enforced at the tool boundary rather
   than in the prompt.

3. **Pick your first course.** The
   [recommended order](TUTOR_COURSE_GUIDE.md#recommended-order) groups the
   courses into three modules and a capstone. Start with the required
   **Agent core**, step 1, and finish it with the required **Capstone**.
   Already know some of it? `uv run agentic-pm-lab placement` asks 12
   concept questions and says which required courses you can skip ahead to
   the quiz; it records nothing.
   Add the optional **Finance domain** module to apply it to investing
   ([pm-mechanics](https://github.com/navoditk/pm-mechanics) teaches the math
   it assumes), and whichever **Platforms** courses match your tools.

4. **Work through that course.** Follow the
   [one-course walkthrough](TUTOR_COURSE_GUIDE.md#use-one-course-from-start-to-finish):
   `agentic-pm-lab course <topic-id>` prints the outline, then read the deep
   dive, trace the code, and do the local lab, failure lab, and build lab.
   The [Depth Path](DEPTH_PATH.md) explains the orient → trace → break →
   teach method behind those steps.

5. **Take the quiz and record it.** `uv run agentic-pm-lab quiz <topic-id>`
   asks 20–35 questions, each citing its source. Passing takes 80% overall
   and 70% in each question tier (concept, implementation, transfer). Then
   `uv run agentic-pm-lab progress` updates
   [`LEARNER_PROGRESS.md`](LEARNER_PROGRESS.md), which tracks what *you*
   understood (`PROGRESS.md` tracks what was built), and prints a
   course-by-tier mastery matrix. `uv run agentic-pm-lab review` brings back
   the concepts your recorded attempts missed, oldest first, as unrecorded
   practice.

6. **Finish with the teach-back.** Explain the topic without notes, cite two
   files, name one simplification, and say what evidence a production claim
   would need. The [completion rubric](TUTOR_COURSE_GUIDE.md#course-completion-rubric)
   lists all five conditions.

7. **Repeat, then do the capstone.** Take the next course in order. After
   Agent core, take the
   [traceability capstone](tutors/traceability-capstone-tutor.md): rebuild one
   decision from a single trace id, then find the hop that drops it. The
   Depth Path's [fixture capstone](DEPTH_PATH.md#a-no-cost-capstone) is an
   optional extension that exercises every layer on a larger question.

## Optional extras

- **Browser UI:** `uv run streamlit run src/ui/app.py` gives you a topic
  selector and the same quizzes, graded in place.
- **Run the whole gate set:** `uv run agentic-pm-lab check` runs every check
  CI runs; seeing it pass locally beats reading a test count in a document.
- **Tutor personas:** in Claude Code, Copilot, or Codex, ask for one tutor by
  name — see [`TUTOR_RUNBOOK.md`](../guides/TUTOR_RUNBOOK.md#how-to-use-one-independently).
  It covers the same content as the CLI, just as a conversation.
- **Canvas walkthrough:** [`CANVAS_EXERCISES.md`](../guides/CANVAS_EXERCISES.md)
  runs one PM question end to end, but needs GitHub Copilot Canvas.
- **How it was built:** the [Phase 1 recap](PHASE_1_RECAP.md) walks through
  the 21-day build day by day, with a self-check list. Its "Tour of the
  build" reads the repository in build order; it complements the course
  order rather than replacing it.
- **Why it is built this way:** the [PRD](../architecture/PRD.md)'s business
  problems and non-goals, then [ARCHITECTURE](../architecture/ARCHITECTURE.md).

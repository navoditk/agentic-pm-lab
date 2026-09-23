# Tutor courses: learner guide

The tutor layer is a set of complete, self-paced local courses. A course is
not just a prompt or a quiz: it combines a tutor persona, deep-dive lessons,
repository tracing, an implementation lab, an adversarial lab, a quiz, and a
teach-back assessment.

The [GitHub Pages curriculum](https://navoditk.github.io/agentic-pm-lab/) and
[standalone HTML artifact](../../artifacts/agentic-pm-curriculum.html) provide
the same reading material and browser-local quizzes without a checkout. They
cannot record durable progress, run code tracing or labs, or establish course
completion; use this local path for those requirements.

For a conversational guide over the same canonical content, open this
checkout in Copilot, Claude Code, or Codex and say **`agentexpert`**. The
[Agentic PM Lab Mastery skill](MASTERY_SKILL.md) selects a path, teaches one
objective at a time, runs source-grounded quizzes and scenarios, and tracks
session progress. The CLI below remains the durable, offline route for quiz
records and works without a Copilot surface.

## Use one course from start to finish

1. List topics:

   ```bash
   uv run agentic-pm-lab learn
   ```

2. Inspect the course outline:

   ```bash
   uv run agentic-pm-lab course aws-agentcore-tutor
   ```

3. Read the linked deep dive and official references. Write down the
   prerequisites, objectives, vocabulary, and one trade-off.
4. Trace the named implementation files and tests. Reproduce one result.
5. Complete the local lab. Use fixtures and mocks; do not substitute a live
   provider result for the repository exercise.
6. Complete the failure lab. Record the expected safe behavior and the
   enforcement or recovery layer responsible for it.
7. Take the quiz:

   ```bash
   uv run agentic-pm-lab quiz aws-agentcore-tutor
   ```

8. Run `uv run python scripts/check_learner_progress.py` to record the quiz
   result. A passing quiz is 80% or higher, but it is not the whole course.
9. Complete the teach-back in the course outline. Explain the topic without
   notes, cite two repository files, name one simplification, and state what
   evidence would be required for a production or live claim.

## Course completion rubric

Mark a topic complete only when all five conditions hold:

- the learner can explain the core concepts and distinguish adjacent concepts;
- the learner can trace and reproduce the repository example;
- the local lab produces the expected result;
- the failure lab produces an explicit safe outcome; and
- the learner passes the quiz and completes the teach-back.

The generated [`LEARNER_PROGRESS.md`](LEARNER_PROGRESS.md) records quiz
comprehension. Keep the lab and teach-back note beside it locally or in a
learning issue; do not put private data or credentials in either record.

## Recommended order

This table is the single source for course order; the README carries the same
generated copy, and `uv run agentic-pm-lab learn` prints it in a terminal.
Only the Agent core module is required. Finance domain and Platforms are
optional; within Platforms, take the courses for the tools you use.
After step 14, finish with the integrated fixture capstone in the
[Depth Path](DEPTH_PATH.md#a-no-cost-capstone).

<!-- LEARNING_PATH:START -->
<!-- Generated from docs/learning/tutor-courses.json by
     scripts/build_learning_path.py. Edit the JSON, not this table. -->

| Step | Module | Course | Topic id | Est. hours |
|---|---|---|---|---|
| 1 | Agent core | [Agent architecture](tutors/agent-architecture-tutor.md) | `agent-architecture-tutor` | ~3 |
| 2 | Agent core | [LangGraph and Deep Agents](tutors/langgraph-deep-agents-tutor.md) | `langgraph-deep-agents-tutor` | ~5 |
| 3 | Agent core | [OpenTelemetry](tutors/opentelemetry-tutor.md) | `opentelemetry-tutor` | ~5 |
| 4 | Agent core | [Evaluations and AgentOps](tutors/evaluation-agentops-tutor.md) | `evaluation-agentops-tutor` | ~5 |
| 5 | Agent core | [Governance and delivery](tutors/governance-delivery-tutor.md) | `governance-delivery-tutor` | ~4 |
| 6 | Finance domain (optional) | [FICC fundamentals](tutors/ficc-tutor-agent.md) | `ficc-tutor-agent` | ~3 |
| 7 | Finance domain (optional) | [Portfolio construction](tutors/portfolio-construction-tutor.md) | `portfolio-construction-tutor` | ~4 |
| 8 | Finance domain (optional) | [Data provenance and research quality](tutors/data-provenance-research-tutor.md) | `data-provenance-research-tutor` | ~3 |
| 9 | Finance domain (optional) | [Public investment data](tutors/investment-data-tutor.md) | `investment-data-tutor` | ~3 |
| 10 | Finance domain (optional) | [Investment committee challenge](tutors/investment-committee-tutor.md) | `investment-committee-tutor` | ~3 |
| 11 | Platforms (optional) | [AWS Bedrock AgentCore](tutors/aws-agentcore-tutor.md) | `aws-agentcore-tutor` | ~4 |
| 12 | Platforms (optional) | [Copilot Canvas and MCP](tutors/copilot-canvas-mcp-tutor.md) | `copilot-canvas-mcp-tutor` | ~3 |
| 13 | Platforms (optional) | [Agent development lifecycle](tutors/agent-development-lifecycle-tutor.md) | `agent-development-lifecycle-tutor` | ~4 |
| 14 | Platforms (optional) | [Document-to-skill pipeline](tutors/document-to-skill-tutor.md) | `document-to-skill-tutor` | ~4 |

Only the Agent core module is required: about 22 hours. The other
modules are optional; take Finance domain to apply the core to investing, and
the Platforms courses for the tools you use. About 53 hours for everything.
Hours are rough estimates covering the deep dive, the three labs, the quiz,
and the teach-back. Each course lists its own prerequisites, so an
experienced learner can start anywhere.

<!-- LEARNING_PATH:END -->

Every course is offline and provider-neutral. Current AWS, LangGraph, and
OpenTelemetry behavior must still be checked against the official references;
the course teaches how this repository uses those systems, not a guarantee of
future vendor APIs.

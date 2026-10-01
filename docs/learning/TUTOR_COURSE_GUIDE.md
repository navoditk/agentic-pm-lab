# Tutor courses: learner guide

The tutor layer is a set of complete, self-paced local courses. A course is
not just a prompt or a quiz: it combines a tutor persona, deep-dive lessons,
repository tracing, an implementation lab, an adversarial lab, a quiz, and a
teach-back assessment.

The [curriculum site](https://navoditk.github.io/agentic-pm-lab/), and the
same page as a single downloadable file
([`artifacts/agentic-pm-curriculum.html`](../../artifacts/agentic-pm-curriculum.html)),
provide the reading material and browser-local quizzes without a checkout. They
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
7. Complete the build lab: write the code yourself, and a test that would
   fail if the behaviour regressed.
8. Take the quiz, which records your attempt:

   ```bash
   uv run agentic-pm-lab quiz aws-agentcore-tutor
   ```

   A passing quiz scores 80% overall and 70% in each question tier
   (concept, implementation, transfer), but it is not the whole course.
   `uv run agentic-pm-lab progress` updates the summary.
9. Complete the teach-back in the course outline. Explain the topic without
   notes, cite two repository files, name one simplification, and state what
   evidence would be required for a production or live claim.

## Course completion rubric

Mark a topic complete only when all six conditions hold:

- the learner can explain the core concepts and distinguish adjacent concepts;
- the learner can trace and reproduce the repository example;
- the local lab produces the expected result;
- the failure lab produces an explicit safe outcome;
- the build lab runs, with a test that would catch a regression; and
- the learner passes the quiz and completes the teach-back.

The generated [`LEARNER_PROGRESS.md`](LEARNER_PROGRESS.md) records quiz
comprehension. Keep the lab and teach-back note beside it locally or in a
learning issue; do not put private data or credentials in either record.

## Recommended order

This table is the single source for course order; the README carries the same
generated copy, and `uv run agentic-pm-lab learn` prints it in a terminal.
Only the Agent core module and the Capstone that follows it are required.
Finance domain and Platforms are optional; within Platforms, take the courses
for the tools you use. The integrated fixture capstone in the
[Depth Path](DEPTH_PATH.md#a-no-cost-capstone) is an optional extension.

<!-- LEARNING_PATH:START -->
<!-- Generated from docs/learning/tutor-courses.json by
     scripts/build_learning_path.py. Edit the JSON, not this table. -->

| # | Course and topic id | Module | Hours |
|---|---|---|---|
| 1 | [Agent foundations](tutors/agent-foundations-tutor.md)<br>`agent-foundations-tutor` | Agent core | ~6 |
| 2 | [Agent architecture](tutors/agent-architecture-tutor.md)<br>`agent-architecture-tutor` | Agent core | ~4 |
| 3 | [LangGraph and Deep Agents](tutors/langgraph-deep-agents-tutor.md)<br>`langgraph-deep-agents-tutor` | Agent core | ~6 |
| 4 | [Model Context Protocol](tutors/mcp-tutor.md)<br>`mcp-tutor` | Agent core | ~4 |
| 5 | [OpenTelemetry](tutors/opentelemetry-tutor.md)<br>`opentelemetry-tutor` | Agent core | ~6 |
| 6 | [Evaluations and AgentOps](tutors/evaluation-agentops-tutor.md)<br>`evaluation-agentops-tutor` | Agent core | ~6 |
| 7 | [Governance and delivery](tutors/governance-delivery-tutor.md)<br>`governance-delivery-tutor` | Agent core | ~5 |
| 8 | [Capstone: traceability end to end](tutors/traceability-capstone-tutor.md)<br>`traceability-capstone-tutor` | Capstone | ~5 |
| 9 | [FICC fundamentals](tutors/ficc-tutor-agent.md)<br>`ficc-tutor-agent` | Finance domain (optional) | ~3 |
| 10 | [Portfolio construction](tutors/portfolio-construction-tutor.md)<br>`portfolio-construction-tutor` | Finance domain (optional) | ~4 |
| 11 | [Data provenance and research quality](tutors/data-provenance-research-tutor.md)<br>`data-provenance-research-tutor` | Finance domain (optional) | ~3 |
| 12 | [Public investment data](tutors/investment-data-tutor.md)<br>`investment-data-tutor` | Finance domain (optional) | ~3 |
| 13 | [Investment committee challenge](tutors/investment-committee-tutor.md)<br>`investment-committee-tutor` | Finance domain (optional) | ~3 |
| 14 | [AWS Bedrock](tutors/aws-bedrock-tutor.md)<br>`aws-bedrock-tutor` | Platforms (optional) | ~4 |
| 15 | [AWS Bedrock AgentCore](tutors/aws-agentcore-tutor.md)<br>`aws-agentcore-tutor` | Platforms (optional) | ~5 |
| 16 | [Copilot Canvas](tutors/copilot-canvas-mcp-tutor.md)<br>`copilot-canvas-mcp-tutor` | Platforms (optional) | ~3 |
| 17 | [Agent development lifecycle](tutors/agent-development-lifecycle-tutor.md)<br>`agent-development-lifecycle-tutor` | Platforms (optional) | ~4 |
| 18 | [Document-to-skill pipeline](tutors/document-to-skill-tutor.md)<br>`document-to-skill-tutor` | Platforms (optional) | ~4 |

Agent core and the Capstone are required: about 42 hours. The other
modules are optional; take Finance domain to apply the core to investing, and
the Platforms courses for the tools you use. About 78 hours for everything.
Hours are rough estimates covering the deep dive, the three labs, the quiz,
and the teach-back. Each course lists its own prerequisites, so an
experienced learner can start anywhere.

<!-- LEARNING_PATH:END -->

Every course is offline and provider-neutral. Current AWS, LangGraph, and
OpenTelemetry behavior must still be checked against the official references;
the course teaches how this repository uses those systems, not a guarantee of
future vendor APIs.

# Tutor courses: learner guide

The tutor layer is a set of complete, self-paced local courses. A course is
not just a prompt or a quiz: it combines a tutor persona, deep-dive lessons,
repository tracing, an implementation lab, an adversarial lab, a quiz, and a
teach-back assessment.

## Use one course from start to finish

1. List topics:

   ```bash
   uv run python scripts/tutor.py
   ```

2. Inspect the course outline:

   ```bash
   uv run python scripts/tutor.py aws-agentcore-tutor --course
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
   uv run python scripts/tutor.py aws-agentcore-tutor --quiz
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

Start with agent architecture, LangGraph/Deep Agents, FICC, and portfolio
construction. Then study provenance and public investment data, followed by
OpenTelemetry, evaluation/AgentOps, governance, and AgentCore. Finish with
Canvas/MCP, investment committee review, document-to-skill, and the integrated
fixture capstone. The courses are independent, so an experienced learner can
start with any topic's prerequisites.

Every course is offline and provider-neutral. Current AWS, LangGraph, and
OpenTelemetry behavior must still be checked against the official references;
the course teaches how this repository uses those systems, not a guarantee of
future vendor APIs.

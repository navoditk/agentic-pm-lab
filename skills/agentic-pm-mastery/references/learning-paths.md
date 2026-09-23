# Learning paths

Choose a route, then resolve each selected topic through
`src/education/tutor.py::TOPIC_CATALOG`. The catalog supplies the current
course, deep dive, persona, quiz bank, and reference anchor.

| Route | Best for | Recommended sequence |
|---|---|---|
| Executive orientation | Understanding scope and proof boundaries in 15 minutes | `README.md` -> `PROGRESS.md` -> `docs/evidence/EVIDENCE.md` |
| Technical walkthrough | Tracing the implemented system in about two hours | `docs/architecture/PRD.md` -> `docs/architecture/ARCHITECTURE.md` -> `docs/guides/RUNBOOK.md` -> one fixture-based capstone run |
| PM foundations | Learning financial reasoning before orchestration | FICC fundamentals -> Portfolio construction -> Public investment data -> Data provenance and research quality |
| Governed agent builder | Designing a safe, observable agent workflow | Agent architecture -> LangGraph and Deep Agents -> Governance and delivery -> Evaluations and AgentOps -> OpenTelemetry |
| Platform integrator | Connecting interfaces and hosted intent without overclaiming evidence | AWS Bedrock AgentCore -> Copilot Canvas and MCP -> Agent development lifecycle -> Document-to-skill pipeline -> Investment committee challenge |
| Full curriculum | Building cross-topic fluency | Follow each course's `step` in `docs/learning/tutor-courses.json` (rendered in `docs/learning/TUTOR_COURSE_GUIDE.md#recommended-order`), then take the final assessment |

All routes are offline by default. The learner may choose any topic after
confirming its prerequisites. Refer to `docs/learning/DEPTH_PATH.md` for the
four-pass orient, trace, break, teach method.

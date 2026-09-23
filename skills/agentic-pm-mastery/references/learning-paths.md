# Learning paths

Choose a route, then resolve each selected topic through
`src/education/tutor.py::TOPIC_CATALOG`. The catalog supplies the current
course, deep dive, persona, quiz bank, and reference anchor.

| Route | Best for | Recommended sequence |
|---|---|---|
| Executive orientation | Understanding scope and proof boundaries in 15 minutes | `README.md` -> `PROGRESS.md` -> `docs/evidence/EVIDENCE.md` |
| Technical walkthrough | Tracing the implemented system in about two hours | `docs/learning/PHASE_1_RECAP.md` "Tour of the build" -> `docs/architecture/ARCHITECTURE.md` -> one fixture-based capstone run |
| Agent core (required) | Mastering agentic AI foundations; start here | Courses whose `stage` is `Agent core`, in `step` order |
| Finance domain (optional) | Applying the core to investing | Courses whose `stage` is `Finance domain`, in `step` order; point to pm-mechanics for the math |
| Platforms (optional) | Learning the tools in the learner's own stack | Courses whose `stage` is `Platforms`; ask which tools they use and take only those |
| Full curriculum | Building cross-topic fluency | Every course in `step` order (rendered in `docs/learning/TUTOR_COURSE_GUIDE.md#recommended-order`), then the final assessment |

Resolve module membership and order from `docs/learning/tutor-courses.json`
at the time of the session, never from memory: the `stage` field names the
module, `required` says whether it is optional, and `step` gives the order.
Recommend Agent core first unless the learner has already passed it.

All routes are offline by default. The learner may choose any topic after
confirming its prerequisites. Refer to `docs/learning/DEPTH_PATH.md` for the
four-pass orient, trace, break, teach method.

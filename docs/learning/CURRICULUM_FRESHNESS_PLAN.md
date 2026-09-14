# Curriculum freshness plan

This plan keeps the **learning curriculum** current without treating a vendor
documentation edit as an automatically correct lesson update. It applies to
the 14-topic course catalog, deep dives, tutor personas, quiz banks, and
mastery skill—not to production code claims or live-provider evidence.

## Operating principle

Automation detects source changes, identifies affected learning assets, and
prepares a review queue. A maintainer validates the technical meaning and
updates the curriculum. The pipeline never silently changes a lesson, answer
key, or evidence claim.

## Phase 1: source registry and asset map

Create `docs/reference/source-registry.yaml` as the canonical external-source
inventory. Each record should include:

| Field | Purpose |
|---|---|
| `id`, `title`, `url`, `kind` | Stable identity and retrieval method (`github_release`, `pypi`, `rss`, `url`). |
| `topics` | Affected tutor IDs from `src/education/tutor.py::TOPIC_CATALOG`. |
| `assets` | Deep dives, personas, quiz banks, and labs requiring review. |
| `version` or `fingerprint` | Last reviewed external state. |
| `last_reviewed`, `review_after_days`, `owner` | Review accountability and expiry policy. |
| `severity_rules` | Terms/releases that require expedited review (breaking, security, deprecated, removed). |

Start with the fast-moving dependencies: LangGraph, Deep Agents, LangSmith,
OpenTelemetry Python/contrib/semantic conventions, MCP Python, AgentCore,
Bedrock Guardrails, GitHub Copilot skills, Claude Code, and Codex. Add data
provider sources only where their user-visible fields or terms are taught.

The asset map must be explicit. For example, a LangGraph change can identify
`langgraph-deep-agents-tutor`, `agent-architecture-tutor`, and their linked
deep dives and quiz banks before a reviewer reads the release notes.

## Phase 2: deterministic validation

Add an offline `scripts/check_curriculum_sources.py` validation command that:

1. validates source-registry schema and unique IDs;
2. verifies every topic and referenced learning asset exists;
3. checks that review dates are not past their policy deadline;
4. ensures the registry topic IDs match `TOPIC_CATALOG`; and
5. checks all required reference URLs syntactically, without network access.

Run it in pull-request CI beside `check_tutor_courses.py`. A new or modified
course that names external behavior must add or update the corresponding
source-registry record.

## Phase 3: scheduled external monitoring

Add a weekly `curriculum-freshness.yml` workflow plus manual dispatch. It
should run a networked monitor in report-only mode:

1. Fetch GitHub release feeds/API, PyPI versions, RSS/Atom feeds, or a
   conditional HTTP response (`ETag`/`Last-Modified`) according to source kind.
2. Compare the observed version/fingerprint with the registry baseline.
3. Emit a machine-readable `curriculum-source-report.json`, retaining the
   previous/current values, checked timestamp, retrieval status, and affected
   topics/assets.
4. Upload the report as an artifact and open or update one deduplicated
   `curriculum-freshness` GitHub issue per material source change.

The monitor must use timeouts, a clear user agent, conditional requests, and
bounded retries. Network failure is reported as `unavailable`; it must not
pretend that a source is unchanged.

## Phase 4: review and change control

Each generated issue uses a checklist:

1. Read the source release note or changed documentation and classify it:
   `no-action`, `clarification`, `behavioral`, `breaking`, or `security`.
2. Confirm how the checked-in code behaves at its pinned dependency version.
3. Update only affected references, deep dives, personas, lessons, labs, and
   quiz questions; cite both the external source and repository code.
4. Update the registry version/fingerprint and `last_reviewed`.
5. Regenerate the standalone curriculum artifact and run all curriculum checks.
6. Update `docs/evidence/EVIDENCE.md` only if a claim about a tested or hosted
   capability changed; a documentation update alone is not evidence.

Require maintainer review for `breaking` and `security` classifications. Do not
automatically merge generated content or quiz answer changes.

## Phase 5: learner-visible freshness

Add per-topic metadata to the generated curriculum and mastery-skill responses:

- external sources reviewed and their pinned version/fingerprint;
- `last_reviewed` date and next review date;
- a visible `review overdue` warning where applicable; and
- a clear distinction between the curriculum review date, repository commit,
  local test evidence, and hosted/production evidence.

This allows a learner to see that an OpenTelemetry lesson was reviewed against
a stated source version without implying that the lab is using or proving the
latest vendor behavior.

## Rollout sequence and acceptance criteria

| Milestone | Acceptance criterion |
|---|---|
| Registry | Every external source taught as a current API has an owner, review cadence, and asset map. |
| Offline CI | Invalid IDs, missing assets, stale review dates, and malformed URLs fail deterministically. |
| Monitor | A controlled fixture proves a changed source creates a deduplicated review issue and report. |
| Review workflow | A sample LangGraph and OpenTelemetry update produces scoped curriculum changes with updated quiz citations. |
| Learner status | The standalone artifact shows review metadata and warns about overdue sources. |

Until the rollout is complete, the curriculum accurately remains current for
the checked-out repository content and relies on learners and maintainers to
consult the official links in `docs/reference/REFERENCES.md` for external API
changes.

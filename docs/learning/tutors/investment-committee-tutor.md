# Investment committee challenge — deep dive

*Companion to [`.github/agents/investment-committee-tutor.agent.md`](../../../.github/agents/investment-committee-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py investment-committee-tutor --quiz`.*

## What this actually is

Most investment-committee failures aren't bad models — they're bad process:
a thesis gets presented, nobody in the room is structurally incentivized to
argue against it, and it passes on momentum rather than evidence. A "Devil's
Advocate" role exists to fix exactly that: someone (or something) whose only
job is to try to disprove the thesis in front of them, before capital moves.
Done well, it surfaces missing evidence, stale data, concentration risk, and
unstated assumptions *before* they become losses, not in the post-mortem.

The hard part of building this into software isn't the checklist — it's
resisting the temptation to let the same system that proposed a trade also
bless it. If the critic and the approver can be the same actor, the challenge
is theater. This repository's investment-committee track is really a study in
one design constraint: how do you make independent challenge and human
approval *structurally* separate, not just procedurally separate.

## Core concepts

- **Thesis.** A structured bundle of claims, supporting evidence, a proposed
  allocation, and (critically) invalidation conditions — what would have to
  be true for this thesis to be wrong.
- **Evidence linkage.** Every claim should point at specific evidence by ID.
  A claim with no linked evidence is not "probably fine" — it's a finding.
- **Coverage vs. severity.** A challenge report doesn't just say pass/fail on
  one axis; it reports which of several independent risk categories were
  checked (coverage) and how serious each finding was (severity), so a
  reviewer can see *what wasn't checked* as clearly as what was.
- **Structural approval separation.** The critic must be unable to approve.
  Not "discouraged from approving" — architecturally incapable of it, and the
  approving human must be a distinct identity from whoever produced the
  thesis.
- **Dissent preservation.** A committee artifact that quietly drops the
  disagreeing view isn't a decision record, it's a rewritten history. The
  workflow's output is designed to keep dissent visible even after a decision
  is made.
- **`pending_human_review`.** Not a status that later resolves itself — a
  terminal state until a distinct human explicitly moves it.

## How this repository implements it

`src/agents/devils_advocate.py`'s `challenge_thesis()` is a deterministic
function, not an LLM call — it takes a thesis dict (`claims`, `evidence`,
`allocation`, `invalidation_conditions`) plus a `decision_date`, and checks it
against exactly seven categories, defined in the `CHALLENGE_CATEGORIES` tuple:
`missing_evidence`, `contradictory_data`, `stale_sources`,
`concentration_risk`, `liquidity_risk`, `unsupported_causality`, and
`invalidation_conditions`. Each check is narrow and explicit: a claim fails
`missing_evidence` if none of its `evidence_ids` resolve to a real evidence
record; it fails `contradictory_data` if any linked evidence item has
`contradicts_claim: True`; a position fails `concentration_risk` if its
`weight` exceeds `max_position_weight` (default 0.25); evidence fails
`stale_sources` if its `publication_date` is older than `max_source_age_days`
(default 30) relative to `decision_date`. Every finding is built by
`_finding()`, which attaches a `category`, `severity`, `subject`, `message`,
and the evidence IDs it's grounded in — read that helper to see exactly what
a "finding" is allowed to claim and what it isn't (it never invents text
beyond the categories above).

There is a separate, optional LLM-backed critic too:
`create_devils_advocate_agent()` builds a Deep Agent with
`tools=()` — an empty tuple. That's not an oversight; it's the enforcement
mechanism. A model with zero bound tools cannot call anything that mutates
state, no matter what its prompt says, so "the critic tried to approve its
own challenge" is not a prompt-engineering risk here, it's a type error.

`run_committee_challenge()` is the workflow wrapper. It always runs
`challenge_thesis()` first, and returns `status: "pending_human_review"`
unless *both* `human_reviewer` and `approval` are supplied. Read the two
explicit guard clauses: `if human_reviewer == "DEVILS_ADVOCATE": raise
PermissionError(...)` and `if role_for_identity(human_reviewer) is None:
raise PermissionError(...)`. The first is the self-approval block named
directly by identity string, not inferred from role — even if someone tried
to register "DEVILS_ADVOCATE" with a normal human role, this specific check
still fires. The second reuses the same `role_for_identity()` control-layer
function every other authorization check in this repository uses (see the
`agent-architecture-tutor` and `governance-delivery-tutor` deep dives), so
committee approval and tool authorization share one identity system, not two.

ADR 0019 (`docs/adr/0019-devils-advocate-committee-challenge.md`) records why
this shape was chosen: the checks are deliberately "conservative and
learning-scale" — they catch explicit evidence-metadata problems (a missing
link, a stale timestamp, an over-concentrated weight), not semantic
contradiction detection. The ADR is explicit that this does not replace human
investment-committee judgment; it's a floor, not a replacement.

## Worked walkthrough

1. Read `challenge_thesis()`'s signature and the `CHALLENGE_CATEGORIES` tuple
   in `src/agents/devils_advocate.py`.
2. Construct a minimal thesis with one claim and no linked evidence:
   ```python
   from src.agents.devils_advocate import challenge_thesis
   thesis = {
       "thesis_id": "T-1",
       "claims": [{"claim_id": "C-1", "evidence_ids": []}],
       "evidence": [],
       "allocation": [{"security_id": "A", "weight": 0.4, "liquidity_status": "illiquid"}],
       "invalidation_conditions": [],
   }
   result = challenge_thesis(thesis, decision_date="2026-01-15")
   ```
3. Inspect `result["findings"]` — you should see four findings:
   `missing_evidence` (claim C-1 has no evidence), `concentration_risk`
   (0.4 > the default 0.25 max), `liquidity_risk` (illiquid), and
   `invalidation_conditions` (the list is empty). Confirm `result["coverage"]`
   lists `contradictory_data`, `stale_sources`, and `unsupported_causality`
   as `uncovered` — this thesis simply didn't give those checks anything to
   examine, which is different from passing them.
4. Now call `run_committee_challenge(thesis, decision_date="2026-01-15")`
   with no `human_reviewer`/`approval` and confirm the status is
   `pending_human_review`.
5. Try `run_committee_challenge(..., human_reviewer="DEVILS_ADVOCATE",
   approval="approve")` and confirm it raises `PermissionError` — this is the
   self-approval block firing.

## Common pitfalls

- **"No findings" is not the same as "verified correct."** A clean
  `challenge_thesis()` result means the seven checks didn't fire — it does
  not mean the thesis is right, only that it cleared a narrow, disclosed set
  of metadata checks. `coverage_ratio` in the result exists specifically so a
  reviewer can see how much of the checklist was actually exercised.
- **Treating the critic's silence as approval.** The Devil's Advocate has no
  tools and produces no approval signal at all — `approved` and
  `critic_may_approve` are hardcoded `False` in every `challenge_thesis()`
  result. There is no code path where the critic's output alone changes
  `status`.
- **Assuming dissent gets cleaned up before the final artifact.** The
  workflow's `result["challenge"]` is carried through unmodified into the
  final committee record even after a human approves — a design choice, not
  a bug, so a later reader can see what was flagged even if it was ultimately
  overruled by a human decision.

## Further reading

- [`docs/reference/REFERENCES.md#tutor-agent-study-map`](../reference/REFERENCES.md#tutor-agent-study-map)
  (this tutor's cited source, the LinqAlpha Devil's Advocate case study on
  Amazon Bedrock, is linked from inside that section).
- `docs/adr/0019-devils-advocate-committee-challenge.md` for the full decision
  record and its consequences.
- `src/agents/multi_agent.py` for how Macro/Quant/Fundamental specialist
  outputs reach the committee stage in the first place (see the
  `agent-architecture-tutor` deep dive for the delegation pattern itself).

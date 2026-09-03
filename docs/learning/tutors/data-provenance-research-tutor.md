# Data provenance and research quality — deep dive

*Companion to [`.github/agents/data-provenance-research-tutor.agent.md`](../../../.github/agents/data-provenance-research-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py data-provenance-research-tutor --quiz`.*

## What this actually is

Data provenance is the discipline of knowing, for every value a system uses,
where it came from, when it was true, when it was published, and under what
terms it may be used. In most software this is a nice-to-have. In an
investment workflow it is load-bearing: a backtest that silently uses a
value that was not yet known at the decision date isn't slightly optimistic,
it's testing a strategy that could not have existed. A research citation
without a retrieval timestamp isn't slightly less rigorous, it's
unfalsifiable — nobody can check it against what was actually published when.

This repository treats provenance as a data-shape problem, not a prose
convention. Every structured observation has a fixed set of required fields;
every piece of evidence has a fixed set of required fields; a function
rejects the record if a required field is missing, rather than a document
merely asking a human to remember to include it.

## Core concepts

- **Observation date vs. release date vs. retrieval time.** The observation
  date is when the underlying fact was true (e.g., "GDP as of Q2 2024"). The
  release date is when that fact was first published. Retrieval time is when
  *this system* fetched it. All three can differ, and only facts whose release
  date is on or before a decision date were actually knowable at that time.
- **Vintage.** A dated snapshot of a data series. The same observation date
  can have multiple vintages if the series gets revised later — vintage is
  what disambiguates "the GDP figure as first published" from "the GDP figure
  as later revised."
- **Point-in-time eligibility.** The test of whether a specific vintage was
  knowable as of a specific decision date — both its observation date *and*
  its release date must be on or before that decision date.
- **Look-ahead bias.** The error of using information in a historical
  decision or backtest that would not actually have been available at that
  point in time. It is the single most common way a backtest quietly
  overstates how good a strategy would have looked.
- **Structured vs. unstructured (evidence) data.** Structured data (prices,
  curves, ratings) can feed a deterministic calculation once it passes
  provenance checks. Unstructured or narrative evidence (filings, thematic
  screens, sentiment) can support retrieval and explanation, but this
  repository's design explicitly forbids it from ever becoming a risk number
  or allocation input on its own.
- **Licensing and redistribution state.** Whether a data value is public,
  fixture-only, or licensed, and whether it may be redistributed — a
  provenance dimension that is easy to omit and expensive to get wrong.

## How this repository implements it

`src/ingestion/provenance.py` is the structured-data half.
`REQUIRED_PROVENANCE_FIELDS` is a literal set —
`{"source", "series_id", "observation_date", "release_date", "unit",
"vintage"}` — and `_validate_observation()` raises if any is missing.
`eligible_as_of(observation, decision_date)` returns `True` only when *both*
`observation_date` and `release_date` are on or before `decision_date`; this
is the actual, callable implementation of "point-in-time eligible," not a
principle stated in a document. `select_point_in_time()` goes one step
further: given multiple vintages of the same `(source, series_id,
observation_date)` key, it picks the *latest eligible* release — i.e., the
most-revised version of the fact that would still have been knowable at the
decision date, not the very first cut.

`src/research/provider.py`'s `mocked_thematic_screen()` is the unstructured
half's evidence shape: `provider`, `publication_time`, `retrieval_time`
(defaults to now if not supplied), a `novelty` score bounded to `[0, 1]`, and
a `licensing` block with `state`/`redistribution`. It validates an empty
query or entity, a malformed ISO timestamp, and an out-of-range novelty score
— each of those checks is a provenance rule made executable rather than
merely documented.

`src/research/fixed_income.py`'s `build_fixed_income_research_bundle()` ties
both halves together for the FICC domain specifically. It only accepts
structured observations whose `topic` is one of six known
`STRUCTURED_TOPICS` (`treasury_auction_supply`, `sofr_funding_conditions`,
`curve_shape`, `trace_liquidity_aggregate`, `issuer_rating_exposure`,
`cftc_rates_positioning`), requires `REQUIRED_PROVENANCE_FIELDS` on each one,
and calls `eligible_as_of()` before including it. Commentary items go through
a separate, evidence-shaped required-field check and always get
`risk_number_eligible: False` stamped onto them — the return value's
`narrative_cannot_create_risk_number: True` flag is the function asserting,
in its own output, the exact boundary described in `docs/architecture/PRD.md`
§2.7: narrative evidence is "evidence and exposure candidates, not a position
instruction."

## Worked walkthrough

Trace what happens to a stale vintage:

1. Read `src/ingestion/provenance.py`'s `eligible_as_of()` and
   `select_point_in_time()`.
2. Construct two vintages of the same observation with
   `make_observation()` — one with `release_date` before a chosen decision
   date, one after.
3. Call `eligible_as_of()` on each against that decision date and confirm
   only the earlier-released one returns `True`.
4. Call `select_point_in_time()` on both together and confirm it returns only
   the eligible one — not the ineligible later vintage, even though it may be
   a more accurate revision of the same fact.
5. Now try `build_fixed_income_research_bundle()` with an observation whose
   `topic` is not in `STRUCTURED_TOPICS` and confirm it raises `ValueError`
   rather than silently accepting an unrecognized topic.

## Common pitfalls

- **Using today's revised value in a historical decision.** A current GDP
  print or current credit rating did not exist at an earlier decision date.
  `eligible_as_of()` exists specifically to catch this — reject the value, or
  select an eligible earlier vintage instead of the current one.
- **Treating "the record has a timestamp" as "the record is provenance-safe."**
  A record needs *both* observation and release timing to be point-in-time
  eligible, plus source, unit, and vintage to be usable at all. A single
  timestamp field is not the same as the full `REQUIRED_PROVENANCE_FIELDS`
  set — `_validate_observation()` will still reject it.
- **Letting narrative evidence answer a numeric question.** A thematic
  screen or sentiment score can motivate a research question or flag
  something worth investigating, but it cannot substitute for a deterministic
  risk or exposure calculation. `build_fixed_income_research_bundle()`'s
  `risk_number_eligible: False` stamp on every piece of commentary is this
  rule enforced in code, not just stated in a prompt.

## Further reading

- [`docs/reference/REFERENCES.md#data-engineering-provenance-and-research-correctness`](../reference/REFERENCES.md#data-engineering-provenance-and-research-correctness)
  and the adjacent
  [`#news-sentiment-and-research-retrieval`](../reference/REFERENCES.md#news-sentiment-and-research-retrieval)
  section.
- `docs/architecture/PRD.md` §2.1's data-contracts-and-provenance fundamental
  and §2.7's external financial-intelligence adapter, which is the source of
  the "evidence, not a position instruction" output-boundary language.
- `tests/unit/ingestion/test_governed_public.py` and the fixed-income branch
  tests under `tests/unit/research/` for concrete pass/fail cases against
  these same functions.

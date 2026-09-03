# Public investment data — deep dive

*Companion to [`.github/agents/investment-data-tutor.agent.md`](../../../.github/agents/investment-data-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py investment-data-tutor --quiz`.*

## What this actually is

Every downstream analytics function in this repository — pricing, risk,
optimization, scenarios — is only as trustworthy as the data feeding it. This
track is about the discipline of *knowing what you actually have*: which
source produced a number, when it was observed, when it was published, what
units it's in, and whether the connector that fetched it is real,
fixture-backed, or aspirational. None of that is optional detail — it's the
difference between a defensible answer and a plausible-sounding guess.

Public investment data splits into two classes with different rules.
Structured data (prices, macro series, curves, positioning) has typed fields
and can feed a calculation directly, once quality-checked. Unstructured or
semi-structured data (filings, news, research narratives) supports retrieval
and explanation, but must never silently become a price, a risk number, or a
portfolio weight. This tutor's whole catalog is organized around that split.

## Core concepts

- **Source catalog.** A single Python dict (`SOURCE_CATALOG` in
  `src/education/investment_data_tutor.py`) is the canonical map of every
  data source this repository knows about — 17 entries as of this writing.
- **Status: real-capable vs. fixture-backed vs. not-yet-integrated.** Every
  catalog entry states this explicitly. "Real-capable" means a connector
  exists and *can* fetch live data (may still need an API key). "Fixture"
  means the sample is invented but shaped like the real thing. Conflating the
  two — claiming a live response was captured merely because a connector
  exists — is exactly what this tutor's negative examples reject.
- **Observation date vs. publication date vs. vintage.** An economic series
  observed on one date is often revised and republished later. The
  *observation date* is what period the value describes; the *vintage* (or
  publication/release date) is when that particular value became known. Using
  today's vintage of a 2020 observation inside a 2020 decision is look-ahead
  bias.
- **Sample file.** Every catalog entry names a small, real, browsable file
  under `data/samples/public_investment/` (or `data/mock_structured/` for the
  two invented CSVs) so a learner can inspect actual shaped records, not just
  a description.
- **Key terms.** Each entry lists the field-level vocabulary a learner needs
  (e.g. ALFRED's `observation date`/`release date`/`vintage`, SEC's `CIK`/
  `XBRL taxonomy`/`accession number`) — the glossary embedded in the catalog
  itself.

## How this repository implements it

`src/education/investment_data_tutor.py` has three public functions.
`list_sources()` returns a compact `{id, name, status}` list for every
catalog entry. `teach_source(source_id, *, browse_sample=False)` returns the
full record plus a fixed `reference` anchor, `read_only: True`, and
`investment_advice: False` — raising `ValueError` with a sorted "choose one
of..." message for an unknown id. `read_sample(source_id)` actually opens the
named file: JSON sources are parsed and validated to be a list of records;
CSV sources are read with `csv.DictReader`, skipping blank lines and `#`
comments. `scripts/investment_data_tutor.py` is a 36-line argparse shim over
these three functions — `scripts/tutor.py`'s generalized CLI follows the
exact same split for all 14 tutor topics.

The catalog's 17 entries split roughly into two tiers. The **high-feasibility**
tier — `sec-companyfacts`, `alfred`, `treasury-auctions`, `sofr`, `cftc-cot`,
`kenneth-french` — has real, tested connector/normalizer code
(`src/ingestion/public_investment.py`), even though none of it is yet
promoted into the canonical DuckDB portfolio tables or claimed as live
experiment evidence. `yfinance-prices` and `fred-macro` are further along —
genuinely live, cached integrations already feeding `src/ingestion/prices.py`
and `src/ingestion/macro.py`. The remaining entries
(`security-master`, `portfolio-positions`, `sec-nport`, `finra-trace`,
`ratings-events`, `gdelt-events`, `bigdata-research`, `openbb-provider`,
`document-pdf`) are explicit mock fixtures — either invented data (the two
structured CSVs) or shaped-but-fictional records standing in for a source
this repository has not yet integrated live, usually for a licensing or
scope reason stated directly in the entry's `status` field.

Look at three entries closely, since they illustrate three different kinds of
"what this can and can't prove":

- **`alfred`** (ALFRED vintage-aware macro data): the sample record carries
  both `observation_date` and `vintage` fields side by side. The entire point
  of this source existing separately from plain FRED is to let a backtest use
  only the value that would have been known on a historical decision date —
  `fred-macro` alone cannot do this.
- **`sec-companyfacts`**: the sample shows `concept`, `unit`, and `value` —
  but the real richness is in the key terms: `CIK`, `XBRL taxonomy`,
  `accession number`, `as-filed`, `amendment`. A single reported number can
  later be amended, and the as-filed value at decision time is not
  necessarily the same as today's "corrected" figure — the same look-ahead
  discipline as ALFRED, applied to filings instead of macro series.
- **`finra-trace`**: explicitly a mock fixture with "licensing and live
  access unresolved." Its `investment_use` field is deliberately hedged: "not
  a complete executable order book" — TRACE tells you about *reported*
  liquidity, not a tradable quote.

## Worked walkthrough

1. List every source: `uv run python scripts/investment_data_tutor.py`.
2. Teach one source with its sample: `uv run python scripts/investment_data_tutor.py alfred --browse`.
3. Confirm the vintage discipline yourself:
   ```python
   from src.education.investment_data_tutor import read_sample
   record = read_sample("alfred")[0]
   print(record["observation_date"], record["vintage"])
   ```
   The two dates differ — that gap is the entire reason ALFRED exists
   separately from a plain current-value macro feed.
4. Compare that against a mock, licensing-blocked source:
   `uv run python scripts/investment_data_tutor.py finra-trace --browse`, and
   read its `status` field closely.
5. Run the real test that pins this catalog's shape:
   `uv run pytest tests/unit/education/test_investment_data_tutor.py -q`.

## Common pitfalls

- **Treating "a connector exists" as "we have live data."** Several
  high-feasibility sources are real-capable but have not yet had a captured
  live response promoted into canonical tables. Say so precisely — capability,
  fixture evidence, and live experiment evidence are three different claims.
- **Using a revised value in a historical decision.** Anything with a
  vintage/observation-date split exists specifically to prevent this. Pulling
  "today's" value into a backtest at an earlier date silently invents
  information the historical decision-maker never had.
- **Treating positioning or sentiment data as a standalone signal.** CFTC
  COT is explicitly weekly and delayed by design; GDELT and provider-research
  entries are narrative evidence, not risk numbers. Both support a decision as
  context, not as the calculation itself.

## Further reading

- [`docs/reference/REFERENCES.md#public-data-terminology-and-decision-use-primers`](../reference/REFERENCES.md#public-data-terminology-and-decision-use-primers)
  and [`#public-data-apis`](../reference/REFERENCES.md#public-data-apis).
- [`data/README.md`](../../../data/README.md) and
  [`data/samples/public_investment/README.md`](../../../data/samples/public_investment/README.md)
  for the full source catalog and field-level explanations.
- [`docs/guides/TUTOR_RUNBOOK.md`](../guides/TUTOR_RUNBOOK.md) for more worked
  and adversarial prompts across the full 17-source catalog.

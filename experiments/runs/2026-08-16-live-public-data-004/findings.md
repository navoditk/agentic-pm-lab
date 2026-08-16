# Findings: live public investment data capture

Run ID: `2026-08-16-live-public-data-004`

## Question and hypothesis

Can approved public-data connectors retrieve bounded live responses and
normalize them into provenance-preserving records before canonical promotion?

## Result

- ALFRED DGS10: `250` observations from vintage `2024-01-02`.
- U.S. Treasury daily yield curve: `2340` tenor records; latest observation `2026-08-14`.
- SEC EDGAR submissions: `1000` normalized filing records for CIK `0000320193`.
- SEC Company Facts: `25135` normalized records, including `699` revenue-related USD records.
- Model tokens: `0`; AWS cost: `$0.00`; public endpoint cost: `$0.00`.

## What worked

Normalized output preserves source URLs, observation dates, release/vintage
semantics, units, CIK, accession numbers, and concept names. Only small
normalized samples and counts are committed; raw provider payloads are not.

## Limitations

The legacy Treasury Fiscal Data auctions path returned HTTP 404 during this
work, so it is not claimed as live evidence. The official Treasury daily
yield-curve XML feed was used instead. ALFRED's public graph CSV exposes the
requested vintage but not every release-history field available through the
keyed FRED API. SEC evidence is metadata and XBRL facts; full filing-text
extraction remains a separate controlled exercise.

## Evidence

- [Normalized response](response.json)
- [Machine-readable manifest](manifest.json)
- [Public data source catalog](../../../data/README.md)

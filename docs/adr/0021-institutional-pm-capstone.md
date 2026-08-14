# ADR 0021: The capstone is a reproducible, governed local replay

## Status

Accepted for Day 20.

## Decision

The institutional PM capstone is implemented as a deterministic local replay
that exercises the complete workflow: PM authentication and portfolio
authorization, point-in-time freshness checks, structured Macro/Quant/FICC
calculations, cited mocked research evidence, Devil's Advocate challenge,
committee artifact generation, explicit human review, OTel/audit emission,
evaluation dimensions, and reproducible data/model/prompt/policy versions.

The fixed-income branch includes a curve-shape shock, credit/spread review,
instrument-term validation, clean/dirty price and accrued-interest assumptions,
and a duration-matching hedge proposal. Missing instrument terms fail before
valuation. No order is generated.

## Consequences

The capstone is a production-oriented proof of concept, not an investment
manager or execution system. Structured calculations and unstructured evidence
are returned in separate provenance paths. The mocked provider is labeled and
live AWS/provider/Canvas capture remains a separate evidence task; the local
evaluation cannot be mistaken for a live deployment acceptance test.

# ADR 0019: Devil's Advocate is independent and approval-free

## Status

Accepted for Day 18.

## Decision

Add a read-only Devil's Advocate agent and a deterministic committee challenge
workflow. The critic receives a thesis, proposed allocation, calculations, and
evidence bundle, then checks missing evidence, contradictions, stale sources,
concentration, liquidity, unsupported causality, and absent invalidation
conditions.

The critic has no bound tools and cannot revise allocations or approve the
committee artifact. The workflow ends in `pending_human_review` unless a
distinct authorized human reviewer explicitly approves or rejects it.

## Consequences

The challenge report is a dissenting artifact, not an investment
recommendation. Findings link back to claim/evidence or allocation subjects and
retain uncertainty through coverage and severity fields. The deterministic
checks are intentionally conservative and learning-scale: they do not claim
semantic contradiction detection beyond explicit evidence metadata or replace
human investment-committee judgment.

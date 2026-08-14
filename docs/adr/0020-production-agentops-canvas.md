# ADR 0020: Extend Agent Operations into the research and committee surface

## Status

Accepted for Day 19.

## Decision

Keep the four-Canvas scope and extend `agent-ops-canvas` with production-facing
research and committee panels rather than adding a fifth Canvas. Shared
handlers expose evidence-provider health, thesis-versus-rebuttal findings,
allocation deltas, fixed-income provenance and hedge assumptions, promotion/SLO
checks, and incident/replay controls.

The Canvas is an interaction surface, not a trust boundary. Handlers do not
call analytics directly or replace Cedar/MCP/tool enforcement. A degraded
provider produces a visible degraded state and suppresses fabricated research.
Promotion remains blocked when live AgentCore evidence is absent or provider
health is degraded.

## Consequences

The operational view can inspect a complete local committee artifact and
exercise outage/dead-letter behavior while keeping live provider, CloudWatch,
LangSmith, and AgentCore integration claims explicit. Fixed-income values that
are not backed by current provenance remain `needs_review` rather than being
filled with estimates.

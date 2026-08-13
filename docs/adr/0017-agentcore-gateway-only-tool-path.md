# ADR 0017: AgentCore Gateway is the deployed tool trust boundary

## Status

Accepted for Day 12.

## Decision

Deployed agents access deterministic tools only through the AgentCore Gateway
MCP target. No deployed Canvas, agent, or Runtime code may call underlying
FastAPI or analytics functions as an alternate production route.

## Rationale

The local MCP adapter centralizes contract validation, identity propagation,
Cedar-equivalent checks, and portfolio entitlement checks. Gateway preserves
the “one Tool Layer, mounted everywhere” design and creates one managed
policy/observability boundary. Direct local calls remain available for unit
tests and development, but are not an accepted deployed path.

## Consequences

Gateway target configuration, AgentCore Policy, and Identity must be captured
before a demo is accepted. A smoke test must prove an authorized request works
and a cross-portfolio request is rejected. Gateway resources must be torn down
after the learning deployment.

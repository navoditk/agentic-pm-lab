# ADR 0018: Research is a separate cited-evidence task graph

## Status

Accepted for Day 17.

## Decision

Use a separate native Deep Agents graph named
`investment-research-supervisor` with three isolated specialists:

- `quantitative-analysis` for deterministic prices, factors, risk, curves, and optimization;
- `news-research` for EDGAR and permitted public evidence;
- `smart-summarizer` for cited structured synthesis and uncertainty.

The graph shares the existing identity-filtered deterministic Tool/MCP
capabilities. Provider adapters return evidence records only. They must include
provider, query, entity, publication time, retrieval time, novelty, licensing,
and a source citation. Narrative evidence cannot create a risk number or
allocation.

## AWS pattern comparison

The AWS investment-research supervisor pattern and this native graph have the
same supervisor-to-specialist shape, but the project keeps orchestration inside
Deep Agents so local tests can inspect routing, isolated context, and recovery
without claiming a live Bedrock Agent deployment.

| Dimension | AWS supervisor pattern | Native project graph |
|---|---|---|
| Routing | Managed supervisor delegates to configured agents/tools | Deep Agents `task` delegation to named subagents |
| Context isolation | Agent/session boundaries depend on service configuration | Each subagent receives only its task context and bound tools |
| Traceability | Cloud service traces and CloudTrail/OTel integration | Existing OTel spans plus specialist attribution |
| Latency/cost | Managed service overhead and model/provider pricing | Local graph overhead; model calls remain measurable through existing telemetry |
| Failure recovery | Service retry/session semantics must be validated in deployment | Existing bounded retries, dead letters, and checkpoint/resume |
| Trust boundary | AgentCore Gateway is the deployed tool route | Same local MCP contract and Cedar re-check remain authoritative |

## Consequences

Structured fixed-income observations can be passed to deterministic analytics
only after point-in-time validation. Unstructured commentary remains cited
evidence and is visible to the summarizer, but cannot be silently converted to
portfolio risk. Live BigData.com, SEC, or AgentCore access remains unclaimed;
the provider fixture is explicitly labeled mocked.

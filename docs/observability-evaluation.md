# Day 6 Observability and Evaluation Evidence

## Unified OpenTelemetry trace

FastAPI, deterministic analytics, the multi-agent hierarchy, identity and
permission checks, and audit writes emit spans through the provider in
`src/observability/telemetry.py`. LangSmith receives that same stream through
OTLP HTTP at `/otel/v1/traces`.

One accepted full-baseline root demonstrates the cross-view identity:

| Field | Value |
|---|---|
| OTel trace ID | `f80cb0ecb15cf52978abde5da9e58250` |
| OTel root span ID | `400262fe5ebc55e3` |
| LangSmith run ID | `00000000-0000-0000-4002-62fe5ebc55e3` |
| Experiment/session ID | `196261c2-6c15-46b2-841d-f828ed02f7a3` |
| Reference example ID | `db201165-bba5-5acb-b8b0-8683ff4bc67a` |

LangSmith derives the root run UUID by padding the native 64-bit OTel root span
ID. The 128-bit OTel trace ID remains the local trace correlation value; the
root span/run pair is the shared identifier across the local exporter and
LangSmith.

## Accepted experiments

| Subset | Experiment | Cases | Input/output tokens | Estimated cost | Total latency |
|---|---|---:|---:|---:|---:|
| Fast | `day6-fast-18ee584c` (`e2fd66ff-efb9-4297-b9ae-1867a5a2afac`) | 5 | 49,007 / 2,703 | $0.0239276 | 78.37 s |
| Full | `day6-full-5bcd4d5c` (`196261c2-6c15-46b2-841d-f828ed02f7a3`) | 15 | 159,416 / 8,530 | $0.0774144 | 363.44 s |

[Open the accepted full experiment trace in LangSmith](https://smith.langchain.com/o/b14067a7-377e-4b5e-b908-e449593f3198/projects/p/196261c2-6c15-46b2-841d-f828ed02f7a3/r/00000000-0000-0000-4002-62fe5ebc55e3?poll=true).

Per-dimension scores and regression tolerance are canonical in
`config/eval-baseline.json`. In the Day 6 snapshot, policy compliance and
guardrail behavior were deliberately unscored rather than counted as passes.

## Day 7 policy extension

Day 7 added three deterministic identity/tool/portfolio cases without spending
model tokens on policy decisions. The accepted full experiment,
`day7-full-450f21c2` (`94f6373f-231c-4c71-9812-55c32d4e1d8e`), ran 18 cases
and scored policy compliance at 100%.

[Open the Day 7 full experiment in LangSmith](https://smith.langchain.com/o/b14067a7-377e-4b5e-b908-e449593f3198/projects/p/94f6373f-231c-4c71-9812-55c32d4e1d8e/r/00000000-0000-0000-93f2-078c6ea5a183?poll=true).

The seven-case fast probe exposed model variability in tool use. Its observed
scores remain recorded separately in `config/eval-baseline.json`; the enforced
fast behavioral floors were not reduced. Guardrail behavior remains unscored
until the Day 12 semantic guardrail cases activate.

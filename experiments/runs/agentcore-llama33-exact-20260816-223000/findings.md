# Findings: Claude Haiku versus Meta Llama 3.3 70B

Run ID: `agentcore-llama33-exact-20260816-223000`

## Method

The same original input, deterministic capstone package, AgentCore Runtime
configuration, region, output limit, and read-only safety boundary were used
for both model runs. Claude was the existing full-capstone run; Llama used the
required cross-region inference profile `us.meta.llama3-3-70b-instruct-v1:0`.

## Results

| Measure | Claude Haiku 4.5 | Meta Llama 3.3 70B |
|---|---:|---:|
| Input tokens | 1,319 | 575 |
| Output tokens | 300 | 300 |
| Total tokens | 1,619 | 875 |
| AgentCore duration/latency | 7,513 ms | 5,915 ms |
| Invocations/sessions | 1 / 1 | 1 / 1 |
| Errors/throttles | 0 / 0 | 0 / 0 |
| Approval required | true | true |
| Order execution | false | false |

Both models produced a committee-oriented risk summary and preserved the
human-review/no-order boundary. Llama used about 46% fewer total tokens and
completed about 21% faster in this single bounded run. This is an observation,
not a quality or pricing conclusion: output was capped at 300 tokens and the
same-day AWS Cost Explorer amount is account-scoped rather than model-attributed.

## Operational finding

Direct invocation of `meta.llama3-3-70b-instruct-v1:0` failed because on-demand
throughput is unsupported in this region. The successful run required the
cross-region inference profile `us.meta.llama3-3-70b-instruct-v1:0`. The direct
failure is retained in `direct-on-demand-error-events.json` as a deployment
lesson.

Private model chain-of-thought was not captured. The comparison uses the
structured capstone trace, observable workflow stages, committee artifact,
token usage, latency, errors, and final safety state.

All temporary Llama runtimes, endpoints, package prefixes, and log groups were
deleted after evidence capture.

# Architecture Diagrams

This document is the visual companion to [`ARCHITECTURE.md`](ARCHITECTURE.md).
The diagrams use Mermaid so they remain editable, reviewable, and renderable in
GitHub. The diagrams describe the current learning-platform design; they do
not imply that every target service or live provider is enabled.

## How to read these diagrams

Read them in this order:

1. Platform layers: where capabilities belong.
2. Request sequence: how one governed request moves through the system.
3. Agent orchestration: how the supervisor delegates work.
4. Data and evidence: what can support calculations versus explanation.
5. Governance: where authority is checked.
6. Deployment comparison: what is local, AWS-backed, or still intended.
7. CI and evaluation: how changes are checked before and after merge.

> **Evidence boundary:** a box labeled `target`, `optional`, or `fixture` is a
> design or learning path, not proof of a live integration. Refer to
> [`EVIDENCE.md`](../evidence/EVIDENCE.md) and [`PROGRESS.md`](../../PROGRESS.md) for evidence.

## 1. Platform layers and trust boundaries

This is the high-level architecture. The Control Layer is deliberately separate
from model reasoning, and the Tool Layer is where deterministic calculations
are exposed through contracts and governed adapters.

```mermaid
flowchart TB
    U[PM or learner] --> I[Interactive Layer<br/>API, Canvas, prompts]
    I --> R[Runtime Layer<br/>local process or AgentCore Runtime]
    R --> A[Agent Layer<br/>supervisor, specialists, context]
    A --> C[Control Layer<br/>identity, Cedar, guardrails, approval]
    C --> T[Tool Layer<br/>FastAPI and MCP contracts]
    T --> D[Data Layer<br/>public data, fixtures, provenance]

    A --> O[Observability<br/>OTel traces, cost, latency, audit]
    T --> O
    C --> O
    O --> E[Evaluation Layer<br/>golden cases and regression]

    X[Automation sub-layer<br/>scheduled review and issue] --> C
    X --> O
```

Key boundary: skills, prompts, and model output may request an action, but only
the Control Layer and final tool boundary can authorize it.

## 2. End-to-end governed request

This sequence shows the normal read-only PM request path. A request can end in
an answer, an abstention, a denial, or human review; it does not become a trade
instruction automatically.

```mermaid
sequenceDiagram
    autonumber
    actor User as PM / learner
    participant Surface as API or Canvas
    participant Control as Identity + Cedar + guardrails
    participant Context as Context builder
    participant Supervisor as PM supervisor
    participant Specialist as Macro / Quant / Fundamental
    participant Tool as Governed MCP or FastAPI tool
    participant Data as Public data or fixture
    participant Evidence as Audit + OTel + evaluation

    User->>Surface: Submit portfolio question
    Surface->>Control: Resolve identity and portfolio entitlement
    Control-->>Surface: Allow, deny, or needs_review
    alt Allowed
        Surface->>Context: Build bounded, point-in-time context
        Context->>Supervisor: Request + filtered context + trace ID
        Supervisor->>Specialist: Delegate domain question
        Specialist->>Control: Request named tool capability
        Control->>Tool: Re-check tool and resource authorization
        Tool->>Data: Read data through contract
        Data-->>Tool: Typed result with provenance
        Tool-->>Specialist: Deterministic result
        Specialist-->>Supervisor: Finding and evidence
        Supervisor->>Control: Check output and approval state
        Control-->>Surface: Answer, abstention, or human-review request
    else Denied or blocked
        Control-->>Surface: Safe denial or guardrail response
    end
    Surface->>Evidence: Record trace, policy, tool, cost, and outcome
```

## 3. Multi-agent orchestration

The supervisor coordinates specialists with restricted tool sets. Specialists
do not receive unrestricted access to the entire analytics layer, and the
supervisor does not treat a narrative response as a substitute for a tool
result.

```mermaid
flowchart LR
    Q[Portfolio question] --> S[Portfolio Manager supervisor]
    S --> M[Macro specialist<br/>rates, regime, liquidity]
    S --> QN[Quant/Risk specialist<br/>exposure, risk, scenarios]
    S --> F[Fundamental specialist<br/>benchmark, attribution, research]
    S --> IR[Research supervisor<br/>quantitative, news, summarizer]
    IR --> DA[Devil's Advocate<br/>contradictions, stale evidence, invalidation]

    M --> MT[Macro tools]
    QN --> QT[Risk, scenario, optimizer tools]
    F --> FT[Attribution and evidence tools]
    IR --> RT[Cited research tools]
    DA --> CT[Committee challenge tools]

    MT --> G[Governed tool boundary]
    QT --> G
    FT --> G
    RT --> G
    CT --> G
    G --> R[Structured findings + citations]
    R --> H[Human review / committee artifact]
```

## 4. Structured data and unstructured evidence

The platform keeps numerical calculation inputs and narrative evidence on
separate paths. This reduces the risk that an extracted sentence silently
becomes a price, risk number, allocation, or execution instruction.

```mermaid
flowchart TB
    subgraph Structured[Structured calculation path]
        P[Prices, curves, macro, positions, instrument terms]
        Q[Identifiers, units, currency, observation and release time]
        V[Point-in-time and quality checks]
        N[Deterministic analytics<br/>pricing, risk, scenarios, optimization]
        P --> Q --> V --> N
    end

    subgraph Unstructured[Unstructured evidence path]
        F[Filings, research narratives, news metadata, model documents]
        X[Extraction, citation, freshness, novelty, injection isolation]
        Y[Retrieval and evidence synthesis]
        F --> X --> Y
    end

    N --> D[Decision-support report]
    Y --> D
    D --> H[Human review]
    N -. cannot directly approve .-> T[Trade execution]
    Y -. cannot directly set risk .-> T
    H -. execution remains out of scope .-> T
```

## 5. Governance and security boundaries

These checks are independent. Authentication identifies the caller; it does
not authorize a tool. Guardrails inspect content; they do not replace policy.
The final tool boundary re-checks authority even when an upstream agent or
Canvas surface has already made a decision.

```mermaid
flowchart LR
    C[Caller] --> AuthN[Authentication<br/>identity and session]
    AuthN --> Ent[Entitlement<br/>portfolio and role]
    Ent --> Policy[Authorization<br/>Cedar tool/resource policy]
    Policy --> Ctx[Context boundary<br/>allowed data only]
    Ctx --> Guard[Guardrails<br/>input, context, output]
    Guard --> Agent[Agent reasoning]
    Agent --> Recheck[Final tool-boundary re-check]
    Recheck --> Tool[Deterministic tool or MCP server]
    Tool --> Approval{Approval required?}
    Approval -->|No| Result[Return bounded result]
    Approval -->|Yes| Human[Authorized human review]
    Human --> Result

    AuthN -. audit .-> Audit[Audit + OTel trace]
    Policy -. audit .-> Audit
    Guard -. audit .-> Audit
    Recheck -. audit .-> Audit
    Human -. audit .-> Audit
```

## 6. Local and AWS deployment comparison

The local path is the primary reproducible learning environment. The AWS path
demonstrates a managed runtime boundary, but optional or account-dependent
components must not be represented as live evidence until they are exercised
and recorded.

```mermaid
flowchart TB
    subgraph Local[Local learning path]
        LSurface[API, Canvas, CLI] --> LAgent[Deep Agents / LangGraph]
        LAgent --> LCedar[Local identity + Cedar + guardrails]
        LCedar --> LMCP[Local MCP / FastAPI tools]
        LMCP --> LData[Public data + DuckDB fixtures]
        LAgent --> LOTel[Local OTel and evaluation]
    end

    subgraph AWS[AWS target and evidence path]
        ASurface[Client or approved entry point] --> ARuntime[AgentCore Runtime]
        ARuntime --> AIdentity[AgentCore Identity / Policy<br/>target or configured]
        AIdentity --> AGuard[Bedrock Guardrails]
        AGuard --> AGateway[AgentCore Gateway<br/>target / optional]
        AGateway --> ATools[Governed MCP tools]
        ATools --> AData[Approved data sources]
        ARuntime --> AObs[CloudWatch / OTel evidence]
    end

    Local -. conceptually maps to .-> AWS
```

The AWS setup and teardown procedure is documented in
[`AWS_AGENTCORE_SETUP.md`](../guides/AWS_AGENTCORE_SETUP.md). A Runtime reaching `READY`
is deployment evidence, not proof that a complete application request succeeded.

## 7. Pull request, evaluation, and release flow

The repository separates code correctness, contract correctness, authorization,
skill freshness, and agent behavior quality into focused GitHub Actions checks.

```mermaid
flowchart LR
    Change[Commit or pull request] --> CI[CI<br/>Ruff + pytest]
    Change --> Contracts[Contract tests<br/>schemas + mocks + negatives]
    Change --> Auth[Authorization tests<br/>Cedar + adversarial cases]
    Change --> Fresh[Skills freshness<br/>code-to-skill alignment]
    Change --> Eval[Evaluation regression<br/>fast PR or full main]
    CI --> Review[Human review and merge]
    Contracts --> Review
    Auth --> Review
    Fresh --> Review
    Eval --> Review
    Review --> Main[main]
    Main --> Progress[Progress tracker<br/>regenerate PROGRESS.md]
    Main --> Release[Reproducible artifact or deployment evidence]
```

See [`GITHUB_WORKFLOWS.md`](../guides/GITHUB_WORKFLOWS.md) for exact triggers,
permissions, local equivalents, and troubleshooting.

## 8. Advanced benchmark evaluation and evidence flow

The original four-model comparison remains the operational baseline. The
advanced scorecard adds deterministic expected-result checks, repeated-run
statistics, qualitative review, and evidence links without overwriting any
baseline response or trace artifact.

```mermaid
flowchart LR
    Input[Canonical PM question<br/>same snapshot + prompt] --> Runs[Four provider runs<br/>OpenAI, Anthropic, AWS Claude, AWS Llama]
    Runs --> Artifacts[Immutable run artifacts<br/>response + manifest + audit]
    Artifacts --> Signals[Observed signals<br/>tokens, cost, latency, retries]
    Artifacts --> Deterministic[Deterministic evaluators<br/>risks, calculations, evidence, governance]
    Artifacts --> Trace[Traceability evidence<br/>OTel, LangSmith, CloudWatch]
    Human[Calibrated PM reviewer] --> Qualitative[Qualitative rubric<br/>usefulness, assumptions, uncertainty, readability]
    Artifacts --> Qualitative
    Signals --> Scorecard[Advanced scorecard<br/>score + confidence + failure taxonomy]
    Deterministic --> Scorecard
    Trace --> Scorecard
    Qualitative --> Scorecard
    Scorecard --> Decision{Promotion gate}
    Decision -->|Pass| Candidate[Candidate for next evaluation stage]
    Decision -->|Fail or critical violation| Remediate[Prompt, policy, data, or model remediation]
```

The scorecard distinguishes automated facts from reviewer judgment. A model
cannot pass promotion with a critical governance failure even if it is cheaper
or faster. Run-level evidence is browsable from
[`INSTITUTIONAL_PM_EVALUATION_SCORECARD.md`](../learning/INSTITUTIONAL_PM_EVALUATION_SCORECARD.md),
while the original baseline remains in
[`CANONICAL_PM_BENCHMARK_REPORT.md`](../learning/CANONICAL_PM_BENCHMARK_REPORT.md).
Scorecard v2 adds the scenario manifest in
`experiments/canonical-pm-benchmark/scenarios/`, repeated-run analysis, p50/p95
latency and variance, and the promotion thresholds in
`config/evaluation-gates.yaml`. Planned scenarios are not counted as observed
evidence.

## Related implementation paths

| Diagram | Primary source of truth |
|---|---|
| Platform layers and security | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Request and agent flow | [`src/agents/`](../../src/agents/), [`src/control/`](../../src/control/) |
| Structured and unstructured data | [`data/README.md`](../../data/README.md), [`src/ingestion/`](../../src/ingestion/), [`src/research/`](../../src/research/) |
| Evaluation and operations | [`src/observability/`](../../src/observability/), [`evals/`](../../evals/), [`experiments/README.md`](../../experiments/README.md) |
| AWS deployment | [`AWS_AGENTCORE_SETUP.md`](../guides/AWS_AGENTCORE_SETUP.md), [`config/agentcore.yaml`](../../config/agentcore.yaml) |
| GitHub Actions | [`GITHUB_WORKFLOWS.md`](../guides/GITHUB_WORKFLOWS.md), [`../../.github/workflows/`](../../.github/workflows/) |

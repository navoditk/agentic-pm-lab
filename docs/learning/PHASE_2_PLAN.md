# Phase 2 Plan: Institutional PM AI Production Readiness

**Status:** Proposed learning track  
**Duration:** 20 working days  
**Audience:** Engineers, quantitative researchers, investment technologists, model-risk partners, platform engineers, and portfolio professionals building a governed PM AI capability at an institutional asset manager  
**Repository posture:** Public/mock data and reversible learning experiments only; no autonomous trading, client data, proprietary data, or production deployment claims

## 1. Purpose

The original 20-day plan established the agentic platform foundation: tools, Deep Agents, LangGraph, MCP, OpenTelemetry, evaluations, Cedar authorization, guardrails, AgentCore, Copilot surfaces, research agents, and an institutional PM capstone.

Phase 2 adds the operating model around that foundation. It focuses on the questions an institutional investment team must answer before an AI-assisted workflow can be promoted beyond a learning proof of concept:

- What investment mandate and risk policy governs the decision?
- Which data is authoritative, licensed, point-in-time eligible, and complete?
- Which calculations are deterministic, and which conclusions are evidence or judgment?
- Who is accountable for the model, data, recommendation, and approval?
- Can the firm reproduce the exact decision months later?
- What happens when the model, provider, tool, identity, or data pipeline fails?
- Can the workflow be evaluated, monitored, rolled back, and audited?

Phase 2 is a production-readiness curriculum, not a request to make the repository an autonomous trading system.

## 2. Relationship to the existing repository

Phase 2 extends, rather than replaces, the original learning path:

| Existing foundation | Phase 2 extension |
|---|---|
| docs/architecture/PRD.md and docs/PLAN.md | Institutional operating requirements and promotion gates |
| src/analytics/ | Mandate-aware fixed-income analytics and risk limits |
| src/ingestion/ and data/ | Data contracts, lineage, quality, entitlement, and evidence graphs |
| src/agents/ | Typed workflow state, bounded plans, abstention, and approval stages |
| src/control/ and governance/ | Production identity, policy exceptions, model risk, and separation of duties |
| src/evals/, evals/, and experiments/ | Repeated trials, grounding, calibration, adversarial, and drift evaluation |
| src/observability/ and AgentOps Canvas | Business-risk telemetry, SLOs, alerts, cost attribution, and incident replay |
| AgentCore Runtime proof | Runtime versus Harness versus Gateway comparison and promotion workflow |
| Day 20 capstone | Reproducible investment decision record and production-readiness review |

Read docs/learning/PLAN_REVIEW.md before starting. The Phase 2 track assumes the original local plan is complete and that its known live gaps remain explicitly labelled rather than silently converted into claims.

## 3. Learning outcomes

At the end of Phase 2, a learner should be able to:

1. Translate an institutional investment mandate into machine-checkable policy.
2. Build point-in-time, licensed, quality-scored investment data flows.
3. Separate structured calculations, retrieved evidence, model judgment, and human approval.
4. Design a typed, resumable, budget-aware multi-agent workflow.
5. Evaluate answer quality, citations, grounding, policy compliance, abstention, stability, cost, and latency.
6. Apply model-risk, data-risk, security, and operational-governance controls.
7. Promote a workflow through CI/CD with signed artifacts, evaluation gates, observability, rollback, and incident evidence.
8. Explain what an AI system did, what it knew at the time, what it did not know, and who approved the resulting investment artifact.

## 4. Non-goals

Phase 2 does not:

- place orders or connect to a broker or execution venue;
- use confidential, client, employee, or proprietary investment data;
- replace a licensed security master, evaluated-pricing feed, or risk system;
- claim regulatory approval or production readiness merely because tests pass;
- make autonomous allocation decisions;
- attempt full high-availability engineering or enterprise-scale data migration;
- require fine-tuning when retrieval, data quality, evaluation, or governance is the real limitation.

## 5. Required artifacts

Each day produces at least one durable artifact under docs/, config/, governance/, contracts/, experiments/, src/, or tests/.

The completed track should contain:

    config/investment_policy.yaml
    config/risk_limits.yaml
    config/data_sources.yaml
    governance/models/model_registry.yaml
    governance/models/model-card-template.md
    governance/models/validation-report-template.md
    contracts/investment_decision_record.schema.json
    contracts/data_quality_report.schema.json
    contracts/evidence_claim.schema.json
    src/control/policy_checks.py
    src/ingestion/data_quality.py
    src/ingestion/lineage.py
    src/research/evidence_graph.py
    src/agents/institutional_workflow.py
    src/evals/phase2_evaluators.py
    experiments/phase2-capstone/
    docs/PHASE_2_LEARNINGS.md

Names may change during implementation, but each concept must remain discoverable and tested.

## 6. Definition of done

Phase 2 is complete when the integrated capstone can demonstrate all of the following with public/mock data:

- a mandate and risk policy are loaded and versioned;
- data sources have owner, license, freshness, point-in-time, and quality metadata;
- every material claim links to an evidence or calculation record;
- the workflow uses typed state and bounded execution limits;
- an unauthorized or unauthenticated caller is rejected at the boundary;
- a policy breach produces breach or needs_review, never a silent pass;
- the agent abstains when evidence is stale, conflicting, missing, or insufficient;
- a human approval is required for a material committee artifact;
- the complete decision record can be replayed from versioned inputs;
- repeated evaluations measure numerical correctness, grounding, citation quality, policy behavior, safety, cost, latency, and stability;
- CI blocks contract, security, evaluation, and dependency regressions;
- an injected provider/model/tool failure produces a controlled degraded result;
- logs and traces are redacted, retained, and access-controlled according to documented policy;
- the capstone records final disposition, reviewer, versions, evidence, limitations, and cleanup state.

Passing unit tests alone is not sufficient evidence for these claims.

## 7. Day-by-day plan

### Day 1 — Phase 2 baseline and institutional use-case selection

**Objective:** Choose one representative institutional workflow and define the target operating model before adding code.

**Work:**

1. Select the primary capstone workflow: duration/curve repositioning review, credit-watchlist review, or liquidity-stress review.
2. Write the user journey from request through final committee artifact.
3. Identify PM, analyst, risk, compliance/model-risk, operations, and platform roles.
4. Classify each step as retrieval, deterministic calculation, model synthesis, policy check, human approval, or publication.
5. Map the workflow to the existing architecture and record gaps.

**Deliverables:** docs/phase2-use-case.md, current/target diagrams, RACI and decision-rights tables, and a Phase 2 baseline experiment manifest.

**Acceptance:** A new learner can explain what the workflow does, who owns each decision, which actions are prohibited, and what evidence proves completion.

### Day 2 — Investment Policy Statement and mandate schema

**Objective:** Convert investment intent into structured, versioned policy.

**Work:** Define benchmark, objective, horizon, eligible assets, prohibited actions, duration bands, spread limits, concentration limits, liquidity rules, escalation thresholds, effective dates, hard versus soft limits, warnings, and approval-only overrides. Create positive, breach, and expired-policy fixtures.

**Deliverables:** config/investment_policy.yaml, config/risk_limits.yaml, policy schema/examples, and tests/unit/control/test_investment_policy.py.

**Acceptance:** A policy check returns pass, warning, breach, or needs_review and identifies the affected rule and position.

### Day 3 — Institutional portfolio and instrument model

**Objective:** Replace the learning-scale position shape with a richer, fixed-income-aware domain model.

**Work:** Extend the security master with identifiers, issuer hierarchy, coupon, maturity, calls/puts, day count, currency, seniority, rating, benchmark, liquidity bucket, and derivative metadata. Extend positions with book, strategy, market value, cost basis, accrued interest, risk measures, and as-of timestamp. Define portfolio, sleeve, mandate, and benchmark relationships. Add unresolved-identifier and incomplete-terms states.

**Acceptance:** No bond enters pricing or risk calculations when required terms are missing or identifiers are unresolved.

### Day 4 — Data contracts, lineage, and quality scoring

**Objective:** Make every source inspectable as a governed data product.

**Work:** Add owner, endpoint, license, entitlement, retention, cadence, timezone, revision behavior, and fallback metadata. Define completeness, freshness, uniqueness, validity, reconciliation, and drift checks. Add a DataQualityReport contract. Record raw snapshot hash, normalized version, transformation, and lineage. Add stale, duplicated, malformed, conflicting, and unauthorized fixtures.

**Deliverables:** config/data_sources.yaml, contracts/data_quality_report.schema.json, src/ingestion/data_quality.py, and src/ingestion/lineage.py.

**Acceptance:** A source can be marked usable, stale, incomplete, conflicted, unlicensed, or unavailable without producing plausible but unqualified output.

### Day 5 — Point-in-time joins and evidence graph

**Objective:** Connect facts, observations, documents, calculations, and claims without losing time semantics.

**Work:** Extend provenance with timezone, publication timestamp, amendment, source snapshot, and eligibility reason. Implement point-in-time joins across holdings, prices, filings, macro data, ratings, and evidence. Create claim, source, snapshot, transformation, tool-result, and conclusion nodes. Add contradiction and duplicate-claim handling.

**Deliverables:** contracts/evidence_claim.schema.json, src/research/evidence_graph.py, point-in-time join tests, and an intentionally ineligible backtest fixture.

**Acceptance:** The system explains why each observation was eligible and why each excluded observation was rejected.

### Day 6 — Document ingestion and RAG baseline

**Objective:** Build a controlled retrieval path for public filings and model documents.

**Work:** Ingest public documents with page and section metadata. Compare fixed-size, semantic, and page-aware chunking. Add issuer, date, document-type, and access-scope filters. Return citations, source spans, retrieval scores, and snapshot IDs. Keep retrieved text in an untrusted-content boundary.

**Acceptance:** Every generated research claim is traced to source spans or explicitly labelled unsupported.

### Day 7 — Retrieval quality, grounding, and indirect injection

**Objective:** Evaluate retrieval and defend against malicious or misleading documents.

**Work:** Add hybrid retrieval and optional reranking. Build a citation-correctness evaluator. Add adversarial documents containing prompt injection, fabricated facts, contradictions, and exfiltration instructions. Measure recall, citation precision, unsupported claims, grounding, latency, and cost. Test guardrail coverage for user input, retrieved text, and tool results.

**Deliverables:** evals/retrieval_cases.jsonl, evals/indirect_prompt_injection_cases.jsonl, RAG findings, and red-team regression tests.

**Acceptance:** Retrieved instructions are treated as data, not authority, and the answer abstains when authoritative evidence is absent or contradictory.

### Day 8 — Fixed-income risk expansion

**Objective:** Add institutional fixed-income risk measures beyond simple price and curve exercises.

**Work:** Implement key-rate duration, DV01, spread duration, convexity, carry, rolldown, curve twists, steepeners, flatteners, butterflies, and spread shocks. Validate units, sign conventions, compounding, settlement, and day count. Compare with hand-calculated toy cases.

**Acceptance:** The system rejects incomplete bond terms and separates price, rate, spread, basis, and liquidity risk.

### Day 9 — Liquidity, transaction cost, and capacity analysis

**Objective:** Teach that an attractive allocation may be unimplementable.

**Work:** Add liquidity buckets, liquidation horizon, bid/ask assumptions, capped-volume interpretation, market-impact scenarios, turnover, capacity, participation, transaction costs, stale prices, sparse OTC observations, and needs-review outcomes.

**Acceptance:** A proposal cannot silently assume every instrument trades at the displayed price and size.

### Day 10 — Mandate-aware constrained optimization

**Objective:** Connect deterministic optimization to policy and implementation constraints.

**Work:** Add duration, spread, issuer, sector, rating, currency, liquidity, turnover, and cash constraints. Compare max-Sharpe, minimum-volatility, risk-parity, robust, and benchmark-relative objectives. Add infeasibility diagnosis. Separate proposed from approved weights. Produce deltas and implementation assumptions.

**Acceptance:** A proposal violating a hard mandate rule cannot proceed without an authorized exception.

### Day 11 — Investment decision record and committee workflow

**Objective:** Make the investment artifact reproducible and accountable.

**Work:** Define the decision-record schema. Link every material claim to evidence, calculation, or policy. Include thesis, counter-thesis, uncertainty, invalidation conditions, dissent, reviewer identity, approval state, timestamps, policy version, expiration, and post-decision review.

**Deliverables:** contracts/investment_decision_record.schema.json, committee artifact generator, approval/rejection fixtures, and an investment-decision auditor agent.

**Acceptance:** A reviewer can reconstruct the decision without hidden model state or an unrecorded conversation.

### Day 12 — Typed agent state and plan-versus-execution workflow

**Objective:** Strengthen the Deep Agent harness with explicit lifecycle state.

**Work:** Define typed state and allowed transitions. Separate plan creation from execution. Add budgets for tokens, tools, retries, time, and cost. Add idempotency keys and durable checkpoints. Add abstention and escalation states.

**Deliverables:** src/agents/institutional_workflow.py, state schema, transition tests, and a plan/execution experiment.

**Acceptance:** Invalid transitions, exceeded budgets, duplicate requests, and unapproved actions fail closed.

### Day 13 — AgentCore Runtime, Harness, Gateway, and identity comparison

**Objective:** Understand where each orchestration and hosting pattern belongs.

**Work:** Run the workflow locally through LangGraph/Deep Agents. Document the AgentCore Runtime path. Add a controlled AgentCore Harness comparison. Configure or safely simulate an HTTPS MCP target for Gateway testing. Compare IAM/SigV4 and OIDC/JWT boundaries. Record model, memory, tool, skill, endpoint, and rollback differences.

**Deliverables:** Runtime-versus-Harness ADR, Gateway target contract or safe local equivalent, identity comparison, and teardown evidence.

**Acceptance:** The learner can explain when Runtime is preferable to Harness, how Gateway changes the trust boundary, and how a caller is authenticated.

### Day 14 — Production authentication, authorization, and policy exceptions

**Objective:** Move beyond local identity lookup to production-shaped identity and exception handling.

**Work:** Validate OIDC/JWT issuer, audience, expiry, and signature. Ensure request-body identity cannot override authenticated identity. Add tenant, portfolio, data-source, and tool entitlements. Add separation of duties. Implement time-bound policy exceptions. Test break-glass access and emergency revocation.

**Acceptance:** Forged identity, cross-portfolio access, expired exceptions, and self-approval are rejected and audited.

### Day 15 — Model-risk management and AI inventory

**Objective:** Treat every model, prompt, agent, retriever, and evaluator as a governed component.

**Work:** Create a model registry with owner, purpose, provider, version, region, data class, materiality, limitations, and approval status. Add model cards, data cards, validation reports, and change logs. Define material versus non-material changes. Add approval gates for model, prompt, skill, tool, and evaluator changes. Record third-party dependency and concentration risk.

**Deliverables:** governance/models/model_registry.yaml, model-card and validation templates, approval workflow, and model-risk tutor.

**Acceptance:** A model or prompt cannot be promoted without ownership, validation evidence, limitations, and approval status.

### Day 16 — Expanded evaluation and repeated-trial stability

**Objective:** Measure decision quality rather than only routing success.

**Work:** Add numerical, unit, citation, grounding, point-in-time, policy, abstention, uncertainty, dissent, and decision-record evaluators. Run important cases repeatedly. Track mean, variance, worst case, confidence intervals, latency, and cost. Compare models, prompts, retrievers, and agent topologies. Add dimension-specific regression gates.

**Deliverables:** src/evals/phase2_evaluators.py, repeated-trial runner, failure taxonomy, and updated AgentOps metrics.

**Acceptance:** A change improving average quality but worsening worst-case policy or citation behavior is not automatically promoted.

### Day 17 — Red-team, privacy, and secure tool-use exercises

**Objective:** Test the complete system against realistic financial-services attack paths.

**Work:** Add direct and indirect prompt injection, tool poisoning, malicious MCP metadata, encoded instructions, untrusted research text, portfolio-data exfiltration, sensitive-output leakage, unsafe code execution, excessive authority, PII classification, redaction, and telemetry exposure tests.

**Deliverables:** red-team case library, privacy and telemetry policy, threat-model update, and remediation backlog.

**Acceptance:** The system fails closed, produces safe audit evidence, and does not disclose secrets or restricted portfolio data.

### Day 18 — CI/CD, infrastructure, and promotion gates

**Objective:** Turn repository checks into an environment-promotion lifecycle.

**Work:** Add IaC validation, security scanning, signed artifacts, SBOM generation, dependency/container/secret/SAST/policy checks, ephemeral environments, contract/security/evaluation/smoke gates, staging approval, canary deployment, rollback, and immutable release metadata.

**Deliverables:** IaC stack or template, release workflow, artifact/SBOM evidence, rollback exercise, and deployment runbook.

**Acceptance:** A deliberately broken contract, policy, evaluator, dependency, or prompt cannot reach promotion.

### Day 19 — Observability, SLOs, cost, capacity, and resilience

**Objective:** Operate the workflow under normal load and controlled failure.

**Work:** Define SLOs for latency, availability, evaluation quality, citation coverage, policy compliance, and cost. Add dashboards and alerts for model, provider, data, tool, and policy failures. Attribute cost by model, portfolio, workflow, and environment. Test quotas, throttling, retries, backpressure, provider outage, stale data, and model fallback. Define RTO, RPO, replay, retention, and incident severity.

**Deliverables:** SLO/alert definitions, capacity and cost report, incident runbook, degraded-provider experiment, and replay evidence.

**Acceptance:** Failure produces a controlled degraded state, alert, incident record, and safe recovery or human escalation path.

### Day 20 — Institutional PM production-readiness capstone

**Objective:** Run the complete governed workflow and conduct a release review.

**Work:** Receive a mock PM request under authenticated identity. Load mandate, policy, positions, market data, and evidence. Run quality and point-in-time checks. Create a bounded plan. Execute deterministic analytics. Retrieve and cite evidence. Run policy, risk, liquidity, and model-risk checks. Generate thesis and counter-thesis. Pause for approval. Produce the decision record. Run repeated evaluations. Replay from the recorded snapshot. Conduct a release-readiness review.

**Deliverables:** experiments/phase2-capstone/manifest.json, experiments/phase2-capstone/findings.md, decision record, trace/audit evidence, evaluation report, release checklist, and retrospective.

**Acceptance:** The result is reproducible, evidence-linked, policy-aware, human-approved, cost-accounted, replayable, and explicitly labelled as a learning proof of concept.

## 8. Suggested Phase 2 tutor and reviewer agents

Add these agents only when their contracts and examples are ready:

| Agent | Purpose |
|---|---|
| investment-process-tutor | IPS, benchmarks, mandate, PM responsibilities, and committee process |
| data-governance-agent | Data cards, lineage, licensing, freshness, identifiers, and quality |
| model-risk-agent | Model inventory, validation, approvals, changes, and limitations |
| production-readiness-agent | CI/CD, IaC, SLOs, secrets, DR, rollback, and operational gaps |
| red-team-agent | Prompt injection, tool poisoning, exfiltration, identity, and guardrail bypass |
| investment-decision-auditor | Citations, calculations, policy results, dissent, approval, and replayability |
| cost-and-capacity-agent | Tokens, retries, quotas, caching, model choice, and cost attribution |

Every agent must have a narrow purpose, read-only default, five worked examples, three negative examples, a contract or response schema, local mocked tests, explicit limitations, escalation behavior, and links to source documents and experiments.

## 9. Phase 2 experiment matrix

Run these with the provider-neutral framework in experiments/README.md:

| Experiment | Variables | Primary measures |
|---|---|---|
| RAG quality | Chunking, metadata, hybrid search, reranking | Recall, citations, grounding, cost, latency |
| Harness comparison | LangGraph, Deep Agents, Runtime, Harness | Control, portability, setup, observability, rollback |
| Model comparison | Local, hosted, Bedrock models | Quality, stability, cost, latency, tool use |
| Policy-aware optimization | Objectives and mandate constraints | Return/risk tradeoff, breaches, infeasibility |
| Red-team resilience | Injection, exfiltration, poisoning, spoofing | Block rate, false positives, safe degradation |
| Provider failure | Stale, unavailable, conflicting, throttled | Abstention, fallback, alerting, replay |
| Repeated-trial stability | Same case across 10+ trials | Variance, worst case, calibration, cost distribution |
| Promotion safety | Broken code, prompt, skill, contract, evaluator | Gate detection and rollback time |

## 10. Recommended implementation order

If the full 20 days cannot be completed, preserve this order:

1. Mandate and policy schema
2. Data quality and point-in-time evidence
3. Decision record and evidence graph
4. Fixed-income risk and liquidity constraints
5. Typed workflow state and abstention
6. Expanded evaluations and red-team cases
7. Model-risk and identity governance
8. CI/CD promotion and rollback
9. SLOs, cost, resilience, and incident replay
10. AgentCore Gateway/Harness and optional comparative exercises

Do not prioritize fine-tuning, additional model providers, or autonomous execution before the earlier controls work.

## 11. Exit review questions

At the end of Phase 2, the learner should be able to answer “yes” or document the gap for each question:

- Can the system prove which mandate and policy version governed the result?
- Can it prove what information was available at the decision time?
- Can every number be reproduced by a deterministic calculation?
- Can every narrative claim be traced to permitted evidence?
- Can the system abstain safely?
- Can an unauthorized user access neither data nor tools?
- Can an approver understand dissent, uncertainty, and invalidation conditions?
- Can the organization identify the model, prompt, skill, data, and code versions?
- Can the workflow be evaluated repeatedly rather than judged from one output?
- Can the release be blocked and rolled back safely?
- Can operations detect cost, latency, provider, policy, and quality degradation?
- Can the entire decision be reconstructed after the fact?

The final answer should be a release-readiness assessment, not a claim that the repository is a production trading platform.


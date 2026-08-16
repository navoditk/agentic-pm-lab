# Findings: managed Guardrail attachment probe

Run ID: `agentcore-managed-guardrail-20260816-215000`

## Result

The managed Bedrock Guardrail was successfully passed to the hosted model
request through `guardrailConfig`. The runtime returned the configured blocked
message and zero model tokens when the request was classified as blocked.

The probe also found a prompt-design false positive: the apparently neutral
portfolio-review request was blocked because the prompt included governance
language and serialized capstone fields. A second neutralized input was also
blocked, so this run does not claim an allowed managed-Guardrail response.

This is distinct from the standalone `ApplyGuardrail` proof, which already
demonstrates an allowed risk question and a blocked trade directive. The
managed attachment path is therefore operationally wired, but its policy and
prompt contract need refinement before it should be promoted.

## Learning outcome

Guardrails classify the complete model input, including instructions and
serialized metadata. Governance field names, safety explanations, and
review vocabulary can create false positives. Production prompt construction
should use a neutral, typed summary envelope and test allowed, borderline,
and blocked cases separately. The deterministic capstone result remains
available outside the model prompt and is returned as structured evidence.

No private chain-of-thought was captured. No order was generated or executed.
All temporary runtimes, package prefixes, log groups, and the Guardrail were
deleted after evidence capture.

# AgentCore portfolio-review experiment

## Objective

Deploy a minimal read-only portfolio-research proof slice to AgentCore Runtime,
invoke it with public/mock Portfolio A evidence, and trace the request.

## Deployment evidence

- Account: `463802498849`
- Region: `us-west-2`
- Runtime reached `READY`.
- Endpoint `default` reached `READY`.
- Runtime ARN: `arn:aws:bedrock-agentcore:us-west-2:463802498849:runtime/agentic_pm_lab_20260813-aAl0i15vuk`
- CodeZip artifact: 19 MB, uploaded with SSE-S3.
- Runtime versions: 1 (macOS package), 2 (S3 read permission correction), 3
  (Linux ARM64 package).

## Execution evidence

The first invocation generated CloudWatch traceback evidence:

```text
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

Diagnosis: the initial zip contained a macOS-native binary. The package was
rebuilt with `aarch64-manylinux2014` wheels and version 3 reached `READY`.

A bounded SDK invocation against version 3 returned:

```text
RuntimeClientError: Received error (500) from runtime.
```

No successful model answer or workflow-stage output was captured. The run is
therefore `deployment_ready_request_failed`, not a successful end-to-end run.

## 2026-08-14 retry

A fresh runtime and endpoint were created from a Linux ARM64 package:

- Runtime ID: `agentic_pm_agentcore_proof_20260813_175047-f6d71VAxMz`
- Runtime and `default` endpoint: `READY`
- Package verification: `pydantic_core` ARM64 Linux extension present
- Stages observed: request received, input validated, authorization allowed,
  orchestration started, execution-role credentials found
- Terminal error:
  `ResourceNotFoundException: Model use case details have not been submitted
  for this account` during Bedrock `Converse`

Conclusion: the runtime and request contract are working through the model
boundary. The remaining blocker is account-level Anthropic model access. An
administrator must submit the Bedrock use-case form and wait for propagation.
The current developer role also cannot delete CloudWatch log groups or list
Guardrails, so two empty log groups remain and a live Guardrails proof is
deferred until the permission set is extended.

## Safe input

See [`input.json`](input.json). It contains only public/mock data.

## Cost and cleanup

- Cost Explorer same-day estimate at capture: `$0.00`.
- Monthly budget: `$50`; final actual `$0.179`, forecast `$0.464`.
- Temporary runtime, endpoint, and S3 artifact: deleted. Two empty log groups
  remain because the current role lacks `logs:DeleteLogGroup`.
- Persistent SSO, roles, organization, account, and budget: retained.

## Follow-up

The reusable minimal fixture and invocation probe are now in
[`experiments/agentcore-runtime-proof/`](../agentcore-runtime-proof/). The
copy/paste deployment, evidence, cost, and teardown procedure is maintained in
[`docs/AWS_AGENTCORE_SETUP.md`](../../docs/AWS_AGENTCORE_SETUP.md). Before the
next live run, reproduce with that fixture and capture its response before
reintroducing dependencies from the full application.

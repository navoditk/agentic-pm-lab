# AWS installation, setup, and end-to-end experiment runbook

This is the operational guide for running the Agentic PM Lab proof experiment
on Amazon Bedrock AgentCore. It takes a new operator from workstation setup to
one traced, read-only request and then removes temporary AWS resources.

The direct S3 CodeZip API path is the canonical path. It is explicit and was
the path used to reach a `READY` runtime during the 2026-08-13 trial. The
AgentCore CLI remains useful for validation, but its generated CDK wrapper can
fail during synthesis before an AWS stack exists.

This experiment uses only public or mock data. It is not investment advice and
does not execute trades.

## 1. Business problem and architecture

The lab demonstrates a read-only institutional portfolio-research workflow.
Given a portfolio snapshot and point-in-time public or mock evidence, it
produces an assessment of rates, credit risk, assumptions, uncertainty, and the
next human-review step.

It addresses three practical problems:

1. Analysts need repeatable analysis over structured evidence without losing
   request identity, source vintage, or assumptions.
2. Portfolio decisions need authorization, guardrails, and a human approval
   boundary. A model must not be able to place an order.
3. Operations teams need to trace a request through identity, policy, model
   invocation, output, cost, and failure evidence.

```text
Operator
  |
  | IAM Identity Center profile -> SigV4 InvokeAgentRuntime
  v
AgentCore Runtime endpoint (PUBLIC network, IAM authorization)
  |
  +-- validate request and record request_id
  +-- record read_only_research / allow decision
  +-- Bedrock Converse through a cross-region inference profile
  +-- return answer, usage, approval_required=true
  |
  +-- CloudWatch Logs: workflow-stage and error evidence

IAM Identity Center -> AWSReservedSSO_AgenticPMLabDeveloper role
Runtime execution role -> S3 CodeZip read + Bedrock invoke + CloudWatch Logs
AWS Budgets / Cost Explorer -> spend guardrail and post-run accounting
```

The full repository also contains Deep Agents, Cedar policy checks, MCP tools,
guardrails, evaluation, and Canvas layers. This proof slice deploys only the
small read-only runtime. Gateway was not created because no HTTPS-hosted MCP
target was in scope.

The observable lifecycle is: authenticate, validate, authorize read-only
research, invoke Bedrock, record usage and guardrail status, emit a response,
then archive logs and cost snapshots. “Reasoning” means these observable
stages and decisions; private model chain-of-thought is not requested or
logged.

## 2. Prerequisites and local setup

Verify these tools:

```bash
aws --version                 # AWS CLI v2; tested with 2.36.19
python3 --version             # Python 3.12 or 3.13
uv --version
node --version                # optional, AgentCore CLI validation
npm --version                 # optional, AgentCore CLI validation
```

From the repository root:

```bash
uv sync --all-groups
```

The first AWS validation should package only
`experiments/agentcore-runtime-proof/`, which contains the small application,
its dependency file, and safe sample input. Do not package the whole repo.

Never put SSO device codes, console tokens, access keys, secret keys, or
passwords in the repo or shell history.

## 3. AWS account and identity setup

### Existing lab configuration

| Item | Value or purpose |
|---|---|
| AWS account | `463802498849` |
| Primary region | `us-west-2` |
| Organization | `o-1q9a561nov`, account governance |
| IAM Identity Center | Human login and temporary credentials |
| Permission set | `AgenticPMLabDeveloper`, one-hour sessions |
| Runtime role | `AgenticPMLabRuntimeExecutionRole` |
| Gateway role | `AgenticPMLabGatewayExecutionRole`, retained for later work |
| Budget | `agentic-pm-lab-monthly`, `$50/month` |
| AWS profile | `agentic-pm-lab` |

If these already exist, do not create a second organization or SSO instance:

```bash
aws configure sso --profile agentic-pm-lab
aws sso login --profile agentic-pm-lab --use-device-code
AWS_PROFILE=agentic-pm-lab aws sts get-caller-identity --output json
```

The result must show the intended account and an
`AWSReservedSSO_AgenticPMLabDeveloper` assumed role. If it shows another
account or root, stop before creating resources.

### Fresh account, administrator-only setup

1. In Organizations, create an organization with **All features**. The service
   itself has no additional charge, but resources remain billable.
2. In IAM Identity Center in `us-west-2`, enable it, create and verify the
   operator user, and create the `AgenticPMLabDeveloper` permission set with a
   one-hour session.
3. Assign that permission set to the lab account and user. The user accepts the
   invitation before running the login command above.
4. Create or retain the runtime and gateway service roles. The runtime role
   trust principal is `bedrock-agentcore.amazonaws.com`.
5. In Bedrock, verify model access in `us-west-2` and use the inference profile
   below if direct on-demand throughput is unavailable.
6. Create a monthly budget. Recommended lab default: `$50`, alerts at 50%, 80%,
   and 100% actual or forecasted spend.

### Caller permission groups

The SSO permission set needs these capabilities, with resource scoping where
the service supports it:

```text
bedrock-agentcore: create/update/delete runtime and endpoint;
  get/list runtime and endpoint; future gateway and policy operations;
  InvokeAgentRuntime. The CLI clients are named
  `bedrock-agentcore-control` and `bedrock-agentcore`, but IAM uses the
  single `bedrock-agentcore` service prefix for both.
bedrock: InvokeModel, InvokeModelWithResponseStream, ApplyGuardrail,
  GetFoundationModel, ListFoundationModels
s3: create bucket, put/get/head/delete object, list bucket, delete bucket
logs: describe groups/streams, filter/get events, delete log group
iam: PassRole for the two lab roles; CreateServiceLinkedRole only for setup
budgets and ce: read-only budget and Cost Explorer access
```

After a permission-set change, wait for provisioning, then run `aws sso logout`
and `aws sso login` again. Existing SSO sessions do not reliably receive new
permissions. The live setup also required the AgentCore Runtime, Gateway
Network, and Network service-linked roles to be initialized once.

### Runtime execution role policy

The runtime role needs CloudWatch Logs write, Bedrock invoke, and read access to
the current CodeZip prefix. Replace placeholders before applying this policy;
do not grant wildcard S3 object permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:us-west-2:ACCOUNT_ID:log-group:/aws/bedrock-agentcore/runtimes/*"},
    {"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource":"*"},
    {"Effect":"Allow","Action":["aws-marketplace:ViewSubscriptions","aws-marketplace:Subscribe","aws-marketplace:Unsubscribe"],"Resource":"*"},
    {"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::CODE_BUCKET/RUN_PREFIX/*"},
    {"Effect":"Allow","Action":"s3:ListBucket","Resource":"arn:aws:s3:::CODE_BUCKET","Condition":{"StringLike":{"s3:prefix":["RUN_PREFIX","RUN_PREFIX/*"]}}}
  ]
}
```

## 4. Preflight and cost guardrail

Use a unique run prefix so cleanup is unambiguous:

```bash
export AWS_PROFILE=agentic-pm-lab
export AWS_REGION=us-west-2
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export RUN_ID="agentcore-proof-$(date +%Y%m%d-%H%M%S)"
export RUNTIME_NAME="agentic_pm_${RUN_ID//-/_}"
export CODE_BUCKET="bedrock-agentcore-code-${ACCOUNT_ID}-${AWS_REGION}"
export RUN_PREFIX="$RUN_ID"
export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/AgenticPMLabRuntimeExecutionRole"
export MODEL_ID="us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

Run these checks before deploying:

```bash
aws sts get-caller-identity --output json
aws bedrock list-foundation-models --by-output-modality TEXT \
  --query 'modelSummaries[?contains(modelId, `claude-haiku`)].modelId' --output table
aws budgets describe-budget --account-id "$ACCOUNT_ID" \
  --budget-name agentic-pm-lab-monthly --output json
python3 -m json.tool experiments/agentcore-runtime-proof/input.json >/dev/null
```

The live trial initially failed with `On-demand throughput isn’t supported`.
The cross-region inference profile in `MODEL_ID` resolved that model-selection
problem.

If the runtime reaches orchestration but CloudWatch records
`Model use case details have not been submitted for this account`, complete the
Anthropic use-case form for the selected Bedrock model in the account's Bedrock
console as an administrator. Wait for model-access propagation, then rerun the
same artifact and endpoint. Do not diagnose this message as a packaging or
AgentCore failure. A diagnostic role may use
`bedrock:GetUseCaseForModelAccess` and
`bedrock:GetFoundationModelAvailability` to verify the account state, but the
current lab developer role is intentionally not granted those account-level
model-access operations.

## 5. Build a Linux ARM64 CodeZip

AgentCore Runtime runs Linux ARM64. A macOS virtual environment in the zip
causes an error such as `pydantic_core._pydantic_core` missing. Build from the
target platform explicitly:

```bash
rm -rf /tmp/agentcore-package-"$RUN_ID"
mkdir -p /tmp/agentcore-package-"$RUN_ID"
cp experiments/agentcore-runtime-proof/agentcore_app.py /tmp/agentcore-package-"$RUN_ID"/
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --target /tmp/agentcore-package-"$RUN_ID" \
  --only-binary=:all: \
  -r experiments/agentcore-runtime-proof/requirements.txt
find /tmp/agentcore-package-"$RUN_ID" -name '*pydantic_core*.so' -print
cd /tmp/agentcore-package-"$RUN_ID"
zip -qr /tmp/"$RUN_ID".zip .
unzip -l /tmp/"$RUN_ID".zip | grep -E 'agentcore_app.py|aarch64-linux-gnu.so' | head
cd - >/dev/null
```

The verification must show a file like
`pydantic_core/_pydantic_core.cpython-313-aarch64-linux-gnu.so`. Do not proceed
if it shows a macOS library or only an x86_64 wheel.

### Full canonical PM benchmark package

The small `agentcore-runtime-proof` fixture is the first smoke test. The
canonical comparison uses the full capstone workflow and must include the
application, `src`, `config`, and `governance` trees:

```bash
export CAPSTONE_PACKAGE=/tmp/agentic-pm-canonical-package
rm -rf "$CAPSTONE_PACKAGE" /tmp/agentic-pm-canonical-package.zip
mkdir -p "$CAPSTONE_PACKAGE"
cp experiments/agentcore-capstone-proof/agentcore_app.py "$CAPSTONE_PACKAGE"/
cp experiments/agentcore-capstone-proof/requirements.txt "$CAPSTONE_PACKAGE"/
cp -R src config governance "$CAPSTONE_PACKAGE"/
uv pip install --python-platform aarch64-manylinux2014 --python-version 3.13 \
  --target "$CAPSTONE_PACKAGE" --only-binary=:all: \
  -r "$CAPSTONE_PACKAGE/requirements.txt"
find "$CAPSTONE_PACKAGE" -name '*pydantic_core*.so' -print
(cd "$CAPSTONE_PACKAGE" && zip -qr /tmp/agentic-pm-canonical-package.zip .)
```

Run both canonical models with the repository runner:

```bash
AWS_PROFILE=agentic-pm-lab uv run python scripts/run_agentcore_benchmark.py \
  --package /tmp/agentic-pm-canonical-package.zip \
  --profile agentic-pm-lab --region us-west-2 \
  --model claude=us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --model llama=us.meta.llama3-3-70b-instruct-v1:0
```

The runner retries only the transient `Runtime initialization time exceeded`
cold-start error. It emits heartbeat polls during runtime and endpoint
creation, records a result only after `hosted-response.json` exists, and waits
for asynchronous endpoint deletion before runtime deletion. If the caller
lacks `bedrock-agentcore:DeleteAgentRuntime`, record the exact permission error
and verify the runtime has disappeared before marking cleanup complete.

## 6. Upload and create the runtime

Create or verify the temporary bucket, upload with SSE-S3, and verify the
object:

```bash
aws s3api head-bucket --bucket "$CODE_BUCKET" 2>/dev/null || \
  aws s3api create-bucket --bucket "$CODE_BUCKET" --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"
aws s3api put-object --bucket "$CODE_BUCKET" --key "$RUN_PREFIX/runtime.zip" \
  --body /tmp/"$RUN_ID".zip --server-side-encryption AES256
aws s3api head-object --bucket "$CODE_BUCKET" --key "$RUN_PREFIX/runtime.zip"
```

Build the tagged-union artifact argument and create the runtime. The command
omits tags because missing `TagResource` permission caused an avoidable failure
in the live trial:

```bash
RUNTIME_JSON=$(python3 - <<'PY'
import json, os
print(json.dumps({
  "codeConfiguration": {
    "code": {"s3": {"bucket": os.environ["CODE_BUCKET"], "prefix": os.environ["RUN_PREFIX"] + "/runtime.zip"}},
    "runtime": "PYTHON_3_13",
    "entryPoint": ["agentcore_app.py"]
  }
}))
PY
)
CREATE_OUTPUT=$(aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name "$RUNTIME_NAME" \
  --description "Read-only AgentCore proof experiment" \
  --role-arn "$ROLE_ARN" --agent-runtime-artifact "$RUNTIME_JSON" \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --protocol-configuration '{"serverProtocol":"HTTP"}' \
  --lifecycle-configuration '{"idleRuntimeSessionTimeout":900,"maxLifetime":3600}' \
  --environment-variables "MODEL_ID=$MODEL_ID" \
  --client-token "$RUN_ID" --region "$AWS_REGION" --output json)
export RUNTIME_ID="$(printf '%s' "$CREATE_OUTPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["agentRuntimeId"])')"
export RUNTIME_ARN="$(printf '%s' "$CREATE_OUTPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["agentRuntimeArn"])')"
printf 'RUNTIME_ID=%s\nRUNTIME_ARN=%s\n' "$RUNTIME_ID" "$RUNTIME_ARN"
```

Poll until `READY`; stop on any failure state:

```bash
for attempt in $(seq 1 30); do
  STATUS=$(aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id "$RUNTIME_ID" --region "$AWS_REGION" \
    --query status --output text)
  printf 'attempt=%s status=%s\n' "$attempt" "$STATUS"
  [ "$STATUS" = READY ] && break
  [[ "$STATUS" == *FAILED* ]] && exit 1
  sleep 10
done
test "$STATUS" = READY
```

## 7. Create the endpoint and invoke

```bash
aws bedrock-agentcore-control create-agent-runtime-endpoint \
  --agent-runtime-id "$RUNTIME_ID" --name default \
  --agent-runtime-version 1 --region "$AWS_REGION" --output json

for attempt in $(seq 1 30); do
  ENDPOINT_STATUS=$(aws bedrock-agentcore-control get-agent-runtime-endpoint \
    --agent-runtime-id "$RUNTIME_ID" --endpoint-name default \
    --region "$AWS_REGION" --query status --output text)
  printf 'attempt=%s endpoint_status=%s\n' "$attempt" "$ENDPOINT_STATUS"
  [ "$ENDPOINT_STATUS" = READY ] && break
  [[ "$ENDPOINT_STATUS" == *FAILED* ]] && exit 1
  sleep 10
done
test "$ENDPOINT_STATUS" = READY

mkdir -p experiments/runs/"$RUN_ID"
uv run python scripts/invoke_agentcore_experiment.py \
  --runtime-arn "$RUNTIME_ARN" \
  --input experiments/agentcore-runtime-proof/input.json \
  --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --output experiments/runs/"$RUN_ID"/response.json
python3 -m json.tool experiments/runs/"$RUN_ID"/response.json
```

The successful response must include the request ID, answer, usage,
`approval_required: true`, `order_execution: false`, and these seven stages:
`request_received`, `input_validated`, `authorization_checked`,
`orchestration_started`, `bedrock_completed`, `guardrail_checked`, and
`response_emitted`. A model answer without these safety fields is not a
successful run.

If a later package version is created, use
`update-agent-runtime-endpoint` to point `default` at that version before
invoking it.

## 8. Capture logs, trace evidence, and cost

Save resource state and CloudWatch evidence before teardown:

```bash
mkdir -p experiments/runs/"$RUN_ID"
aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id "$RUNTIME_ID" \
  --region "$AWS_REGION" > experiments/runs/"$RUN_ID"/runtime.json
aws bedrock-agentcore-control get-agent-runtime-endpoint \
  --agent-runtime-id "$RUNTIME_ID" --endpoint-name default --region "$AWS_REGION" \
  > experiments/runs/"$RUN_ID"/endpoint.json
LOG_GROUP="/aws/bedrock-agentcore/runtimes/$RUNTIME_ID-default"
aws logs describe-log-streams --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime --descending --region "$AWS_REGION" \
  > experiments/runs/"$RUN_ID"/log-streams.json
aws logs filter-log-events --log-group-name "$LOG_GROUP" \
  --start-time "$(( $(date +%s) - 3600 ))000" --region "$AWS_REGION" \
> experiments/runs/"$RUN_ID"/events.json

# AgentCore may also create an uppercase endpoint-suffix group. Query both when
# troubleshooting delivery, but the lowercase `-default` group contains the
# normal endpoint event stream for this lab.
UPPER_LOG_GROUP="/aws/bedrock-agentcore/runtimes/$RUNTIME_ID-DEFAULT"
aws logs describe-log-streams --log-group-name "$UPPER_LOG_GROUP" \
  --order-by LastEventTime --descending --region "$AWS_REGION" \
  > experiments/runs/"$RUN_ID"/log-streams-DEFAULT.json 2>/dev/null || true
aws budgets describe-budget --account-id "$ACCOUNT_ID" \
  --budget-name agentic-pm-lab-monthly > experiments/runs/"$RUN_ID"/budget.json
```

Correlate with `request_id`, `runtimeSessionId`, and the runtime ID. Expected
messages include `workflow_stage=request_received`, `input_validated`,
`authorization_checked`, `orchestration_started`, `bedrock_completed`,
`guardrail_checked`, and `response_emitted`. Log delivery can lag 30-60
seconds; query again before concluding that evidence is absent.

Cost drivers are runtime compute, Bedrock input/output tokens, temporary S3
storage and requests, and CloudWatch Logs. The proof slice caps output at 300
tokens and uses the Haiku inference profile. IAM Identity Center,
Organizations, and a standard budget have no per-request inference charge.
Cost Explorer is delayed, so capture it separately and label it estimated:

```bash
START_DATE="$(date +%F)"
END_DATE="$(date -v+1d +%F 2>/dev/null || date -d tomorrow +%F)"
aws ce get-cost-and-usage --time-period Start="$START_DATE",End="$END_DATE" \
  --granularity DAILY --metrics UnblendedCost \
  > experiments/runs/"$RUN_ID"/cost.json
```

The 2026-08-13 budget snapshot was `$0.179` actual and `$0.464` forecast;
same-day Cost Explorer showed `$0.00` while billing data was still settling.

## 9. Teardown and verification

Delete temporary resources in this order. Never delete the organization, SSO
instance, shared roles, or budget for an individual experiment:

```bash
aws bedrock-agentcore-control delete-agent-runtime-endpoint \
  --agent-runtime-id "$RUNTIME_ID" --endpoint-name default --region "$AWS_REGION"
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-id "$RUNTIME_ID" --region "$AWS_REGION"
aws s3api delete-objects --bucket "$CODE_BUCKET" \
  --delete "$(aws s3api list-objects-v2 --bucket "$CODE_BUCKET" \
    --prefix "$RUN_PREFIX/" --query '{Objects: Contents[].{Key:Key}}' --output json)" \
  2>/dev/null || true
aws s3api delete-bucket --bucket "$CODE_BUCKET" --region "$AWS_REGION" 2>/dev/null || true
for suffix in DEFAULT default; do
  aws logs delete-log-group \
    --log-group-name "/aws/bedrock-agentcore/runtimes/$RUNTIME_ID-$suffix" \
    --region "$AWS_REGION" 2>/dev/null || true
done
```

Verify cleanup:

```bash
aws bedrock-agentcore-control list-agent-runtimes --region "$AWS_REGION" \
  --query "agentRuntimes[?agentRuntimeName=='$RUNTIME_NAME']" --output json
aws logs describe-log-groups --log-group-name-prefix \
  "/aws/bedrock-agentcore/runtimes/$RUNTIME_ID" --region "$AWS_REGION"
```

For a shared bucket, delete only the run prefix and retain the bucket.

## 10. Troubleshooting from the live setup

| Symptom | Cause and resolution |
|---|---|
| `On-demand throughput isn’t supported` | Use the cross-region inference profile and verify Bedrock model access. |
| `CreateWorkloadIdentity` `AccessDenied` | Add both parent and child workload-identity-directory resource scopes, reprovision the permission set, and refresh SSO. |
| `TagResource` `AccessDenied` | Omit tags for the proof run or add narrowly scoped tag permission. |
| Service-linked-role creation failure | Initialize the documented AgentCore Runtime, Gateway Network, and Network service-linked roles with administrator permission. |
| `InvokeAgentRuntime` `AccessDenied` | Add the action to the SSO permission set, wait for provisioning, log out/in, and repeat the identity check. |
| `pydantic_core` import error | Rebuild with `--python-platform aarch64-manylinux2014` and inspect the ARM64 `.so`. |
| Runtime `READY`, invocation HTTP 500 | Inspect CloudWatch, save the traceback, and reproduce with the minimal fixture before adding dependencies. |
| `aws-marketplace:ViewSubscriptions` or `aws-marketplace:Subscribe` denied | Add `ViewSubscriptions`, `Subscribe`, and `Unsubscribe` to the runtime execution role; wait a few minutes for first-account model subscription completion, then retry. |
| No CloudWatch events immediately | Wait 30-60 seconds; verify the execution role can create streams and put events. |
| AgentCore CLI reports no stack | Set a writable `UV_CACHE_DIR`, verify credentials, and use this direct CodeZip path. |

## 11. Current setup summary and evidence

Persistent setup retained for future experiments:

- Organization `o-1q9a561nov`: account governance.
- Account `463802498849`: lab workload account.
- IAM Identity Center instance: human SSO and temporary credentials.
- `AgenticPMLabDeveloper`: one-hour operator permission set.
- `AgenticPMLabRuntimeExecutionRole`: scoped runtime service permissions.
- `AgenticPMLabGatewayExecutionRole`: retained for a future HTTPS/MCP path.
- `agentic-pm-lab-monthly`: `$50` spend guardrail.

The final 2026-08-14 deployment reached `READY`, including endpoint `default`,
and a bounded SDK invocation returned a successful model answer. Earlier
iterations proved the macOS-wheel and model-access failure modes. All temporary
runtime, endpoint, S3 artifact, and evaluation resources were deleted after
evidence capture. The successful run and optional capability results are
recorded in [`docs/evidence/EVIDENCE.md`](../evidence/EVIDENCE.md):

- [`experiments/2026-08-13-agentcore-pm-review/`](../../experiments/2026-08-13-agentcore-pm-review/)
- [`experiments/agentcore-runtime-proof/`](../../experiments/agentcore-runtime-proof/)

AgentCore IAM note: the CLI client names `bedrock-agentcore-control` and
`bedrock-agentcore`, but IAM uses the single `bedrock-agentcore` service prefix
for actions from both clients. AgentCore Evaluations also requires the caller
and evaluation execution role to query CloudWatch Logs; the minimal fixture
must emit the required ADOT/OTel trace attributes or an evaluation can complete
with zero sessions.

### 11a. On-demand Evaluation from a saved span fixture

For a direct evaluator test, keep a JSON request containing `evaluatorId`, an
`evaluationInput.sessionSpans` array, and optional trace-level reference
inputs. The fixture in
`experiments/agentcore-runtime-proof/evaluation_input.example.json` is
synthetic and safe to reuse:

```bash
AWS_PROFILE=agentic-pm-lab aws bedrock-agentcore evaluate \
  --region us-west-2 \
  --cli-input-json file://experiments/agentcore-runtime-proof/evaluation_input.example.json \
  --output json
```

Supported evaluation spans need a supported scope such as
`strands.telemetry.tracer`, a matching event with the same `traceId` and
`spanId`, `attributes.session.id`, `attributes.event.name`, and an event body
with input/output messages. A span-only or application-log-only fixture may
complete with zero sessions or return `LogEventMissingException`/
`AgentSpanMappingException`. The successful lab fixture returned
`Builtin.Helpfulness` value `0.33` and 1,034 evaluator tokens. For a hosted
runtime, use Strands OTEL instrumentation and collect the corresponding
CloudWatch spans/events before evaluating. LLM-judge values can vary between
identical calls; record the returned value and evaluator token usage for each
run rather than asserting an exact score.

## 12. AWS references

- [Deploy code to an AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html)
- [CreateAgentRuntime API](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_CreateAgentRuntime.html)
- [AgentCore Runtime permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- [AgentCore service-linked roles](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/service-linked-roles.html)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [AgentCore on-demand evaluation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/getting-started-on-demand.html)
- [AgentCore input span format](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/understanding-input-spans.html)
- [AWS Budgets pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/)
- [AWS Organizations pricing](https://docs.aws.amazon.com/organizations/latest/userguide/pricing.html)

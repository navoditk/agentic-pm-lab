# AgentCore Gateway target exercise

This guide implements the missing Gateway evidence for the original plan. It
creates a small regional API Gateway REST API backed by a read-only Lambda,
then exposes three GET operations as AgentCore Gateway tools. The payloads are
public/mock learning data only; the exercise cannot place orders or access
portfolio holdings.

## Architecture

```text
AgentCore Gateway (MCP, AWS_IAM authorizer)
  |  GATEWAY_IAM_ROLE -> execute-api:Invoke
  v
API Gateway REST API (regional, HTTPS, IAM-authenticated)
  |  AWS_PROXY
  v
Lambda (deterministic public/mock payloads)
  |
  +-- /portfolio/risk
  +-- /market/curve
  +-- /research/evidence
```

The deployable CloudFormation template and OpenAPI source are in
[`infrastructure/agentcore-gateway-target/`](../../infrastructure/agentcore-gateway-target/).

## Prerequisites

- AWS CLI v2.13.22 or later.
- A valid `agentic-pm-lab` IAM Identity Center session.
- AgentCore Gateway create/get/delete and target create/get/delete permissions.
- CloudFormation permissions to create the lab stack and named IAM roles.
- The existing `AgenticPMLabGatewayExecutionRole`, or an equivalent role
  trusted by `bedrock-agentcore.amazonaws.com`.
- The Gateway role must be allowed to call only this API stage:

```json
{
  "Effect": "Allow",
  "Action": "execute-api:Invoke",
  "Resource": "arn:aws:execute-api:us-west-2:ACCOUNT_ID:REST_API_ID/lab/GET/*"
}
```

Replace placeholders at deployment time; never commit credentials.

## Deployment steps

```bash
export AWS_PROFILE=agentic-pm-lab
export AWS_REGION=us-west-2
export STACK_NAME=agentic-pm-gateway-target

aws sts get-caller-identity
aws cloudformation validate-template \
  --template-body file://infrastructure/agentcore-gateway-target/template.yaml \
  --region "$AWS_REGION"

aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file infrastructure/agentcore-gateway-target/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION"

aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region "$AWS_REGION"
```

The API uses AWS_IAM authorization. An unsigned request should fail with
`403`; do not make the API public to bypass this test.

## Create the AgentCore Gateway and target

Resolve the existing Gateway role ARN and add the stage-scoped
`execute-api:Invoke` permission above. Then create the Gateway:

```bash
export GATEWAY_ROLE_ARN='arn:aws:iam::ACCOUNT_ID:role/AgenticPMLabGatewayExecutionRole'

aws bedrock-agentcore-control create-gateway \
  --name agentic-pm-lab-gateway \
  --description 'Read-only Agentic PM Lab MCP gateway target' \
  --role-arn "$GATEWAY_ROLE_ARN" \
  --protocol-type MCP \
  --protocol-configuration '{"mcp":{"supportedVersions":["2025-03-26"],"instructions":"Expose only read-only public/mock investment research tools.","streamingConfiguration":{"enableResponseStreaming":false}}}' \
  --authorizer-type AWS_IAM \
  --region "$AWS_REGION"
```

Create the API Gateway target using the `RestApiId` and `StageName` outputs:

```bash
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier GATEWAY_ID \
  --name pm-read-only-api \
  --description 'Read-only API Gateway operations for PM learning' \
  --target-configuration '{"mcp":{"apiGateway":{"restApiId":"REST_API_ID","stage":"lab","apiGatewayToolConfiguration":{"toolFilters":[{"filterPath":"/portfolio/risk","methods":["GET"]},{"filterPath":"/market/curve","methods":["GET"]},{"filterPath":"/research/evidence","methods":["GET"]}]}}}}' \
  --credential-provider-configurations '[{"credentialProviderType":"GATEWAY_IAM_ROLE","credentialProvider":{"iamCredentialProvider":{"service":"execute-api","region":"us-west-2"}}}]' \
  --region "$AWS_REGION"
```

Poll until the target status is `READY`. `FAILED`,
`UPDATE_UNSUCCESSFUL`, and `SYNCHRONIZE_UNSUCCESSFUL` require inspecting
`statusReasons` and CloudTrail before retrying.

```bash
aws bedrock-agentcore-control get-gateway --gateway-identifier GATEWAY_ID --region "$AWS_REGION"
aws bedrock-agentcore-control get-gateway-target \
  --gateway-identifier GATEWAY_ID \
  --target-id TARGET_ID \
  --region "$AWS_REGION"
```

## Evidence and observations

Capture a dated directory under `experiments/runs/` containing:

1. CloudFormation validation and stack outputs.
2. Gateway and target JSON, with ephemeral tokens and secrets removed.
3. Target status reaching `READY`.
4. Generated tool names and descriptions.
5. One successful read-only call for each operation.
6. One denied call proving the IAM boundary.
7. CloudTrail/CloudWatch request evidence and latency/error metrics.
8. The exact runtime request that consumed the tools, if a runtime is connected.
9. Stack and Gateway deletion responses proving cleanup.

Never record private chain-of-thought; the supported audit artifact is the
ordered workflow/event trace and visible tool response.

The first live preflight on 2026-08-17 reported AWS CLI `2.36.22`, but the SSO
token for `agentic-pm-lab` had expired and refresh failed. No Gateway or target
was created. This is an authentication-session blocker, not a template failure.

Expected lessons from the live run:

- API Gateway supplies the real TLS/HTTPS boundary.
- AgentCore Gateway converts selected REST operations into MCP tools using
  operation IDs, descriptions, and tool filters.
- A `READY` target does not prove successful calls; the Gateway role also needs
  stage-scoped SigV4 `execute-api:Invoke` permission.
- Authentication, tool authorization, and portfolio entitlement are separate
  controls and should be evidenced independently.
- Gateway status, target synchronization, generated tools, and API responses
  are separate evidence points.

## Teardown

Delete the target before the Gateway, then delete the CloudFormation stack:

```bash
aws bedrock-agentcore-control delete-gateway-target \
  --gateway-identifier GATEWAY_ID --target-id TARGET_ID --region "$AWS_REGION"
aws bedrock-agentcore-control delete-gateway \
  --gateway-identifier GATEWAY_ID --region "$AWS_REGION"
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
```

Confirm that no stack, Gateway, target, Lambda, API, or retained log group
remains. Keep sanitized evidence and lessons learned, not live resources.

# AWS Bedrock — deep dive

*Companion to [`agents/aws-bedrock-tutor.md`](../../../agents/aws-bedrock-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz aws-bedrock-tutor`.*

This Platforms course assumes [Agent foundations](agent-foundations-tutor.md).
It comes before [AWS Bedrock AgentCore](aws-agentcore-tutor.md): Bedrock is
the model layer, AgentCore the runtime around an agent. No lab calls AWS.
Every call goes through botocore's `Stubber`, which validates each request and
response against the Bedrock service model shipped with the SDK, so a wrong
field name fails a test rather than a production call.

## What this actually is

Amazon Bedrock hosts foundation models from several providers behind one
service. For an agent, the part that matters is the model call. The
[Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
"provides a consistent API that works with all Amazon Bedrock models that
support messages. This means you can write code once and use it with
different models." Calling it needs the `bedrock:InvokeModel` permission;
`ConverseStream` needs `bedrock:InvokeModelWithResponseStream`.

The central fact for an agent builder is in the
[tool-use guide](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html):
"the model doesn't directly call the tool." The model returns a request; your
code runs the tool and sends the result back. So everything Agent foundations
put in the loop (the allowlist, the spans, the audit trail) stays in your
code when the model moves to Bedrock.

## Core concepts

- **Tool use through Converse.** The model ends its turn with
  `stopReason: "tool_use"` and `toolUse` blocks (`toolUseId`, `name`,
  `input`). Your code returns `toolResult` blocks in a **user** message, with
  `status: "error"` when the tool failed. Converse messages alternate between
  user and assistant, so several results for one turn go in one message.
- **Inference profiles.** A [cross-Region inference profile](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
  is predefined by Bedrock and routes a model's requests across several
  Regions; you pass its ID as the `modelId`. Application inference profiles
  add cost and usage tracking.
- **Least-privilege IAM.** When a policy names an inference profile, AWS says
  "you must also specify the foundation model in each Region associated with
  it", and a condition can restrict those models to calls made through the
  profile ([prerequisites](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html)).
- **Throttling.** A `ThrottlingException` (HTTP 429) means an account quota
  was exceeded. AWS recommends
  [retries with exponential backoff and jitter](https://docs.aws.amazon.com/bedrock/latest/userguide/troubleshooting-api-error-codes.html),
  checking quotas, and Provisioned Throughput or a quota increase for
  sustained load. Access and validation errors fail identically on every
  attempt and are not retried.
- **Guardrails as an API.** A guardrail can be attached to a Converse call
  (`guardrailConfig`; a blocked turn ends with `stopReason:
  "guardrail_intervened"`), or used on its own through
  [ApplyGuardrail](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html),
  which evaluates text "without invoking the foundation models". AWS's
  example: check a user's input before retrieval runs in a RAG application.
- **Prompt caching.** A `cachePoint` marks the end of a stable prefix. It is
  cached only if the prefix meets the model's minimum token count; otherwise
  "your inference still succeeds, but your prefix isn't cached". With caching,
  `inputTokens` "represents only the non-cached input tokens", so total input
  is `inputTokens + cacheReadInputTokens + cacheWriteInputTokens`
  ([prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)).
- **Knowledge Bases.** Managed retrieval-augmented generation over your data
  sources, with optional citations back to the source
  ([Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)).
  `Retrieve` returns matching chunks for your own prompt;
  `RetrieveAndGenerate` also writes the answer and returns its citations.

## How this repository implements it

`src/runtime/bedrock_lab.py` holds the lab. `ConverseModel` is a Bedrock model
behind the Agent foundations model interface: it builds the Converse request
from the loop's transcript (`to_converse_messages`) and allowed tool specs
(`tool_config`), and turns the response back into a `ModelTurn`. Because only
the model changed, `run_agent()` runs unchanged, with its allowlist, spans,
and audit trail. The chat span carries `gen_ai.provider.name: aws.bedrock`,
token usage, and the finish reason, by the OpenTelemetry GenAI conventions.

`with_retries()` retries `ThrottlingException`, `ServiceUnavailableException`,
`ModelNotReadyException`, and `InternalServerException` with bounded
exponential backoff and full jitter, and raises everything else at once.
`apply_guardrail()` wraps ApplyGuardrail. `total_input_tokens()` implements
AWS's formula. `invoke_through_profile_policy()` builds the two-statement
policy from AWS's prerequisites page.

### A limitation of offline labs

In production, botocore retries throttling itself, with its `legacy`,
`standard`, and `adaptive` retry modes. Under `Stubber`, it does not:
`test_stubber_bypasses_botocores_own_retries` shows a stubbed throttle is
raised on the first attempt. The lab's explicit `with_retries()` is what the
tests can observe; it is not a reason to disable botocore's retries.

## The four threads

| Thread | With Bedrock as the model | Evidence |
|---|---|---|
| **Observability** | The chat span records `aws.bedrock`, input and output tokens (cached tokens included), and the finish reason. | `test_the_chat_span_records_bedrock_usage_by_the_genai_conventions` |
| **Traceability** | The Bedrock chat span and every audit record share the run's trace id. | same test |
| **Governance** | Only allowed tools are offered in `toolConfig`; a forbidden `toolUse` is refused by `governed_call`, because Bedrock never runs tools. IAM is scoped to one model through one profile. A guardrail filters content; it does not replace the allowlist. | `test_a_failed_tool_goes_back_with_error_status_and_a_forbidden_one_is_refused`, `test_an_inference_profile_policy_also_names_each_regions_model` |
| **Evaluation** | Switching the model is a behaviour change: rerun the same eval cases through the unchanged loop, over repeated trials, with the graders from Agent foundations. | `src/foundations/grading.py` |

## Worked walkthrough

1. Run the course's tests:
   ```bash
   uv run pytest tests/unit/runtime/test_bedrock_lab.py -q
   ```
2. Read `test_the_agent_loop_runs_unchanged_with_bedrock_as_its_model`. Find
   the expected second request and point to the `user` message carrying the
   `toolResult`.
3. Read `test_throttling_is_retried_with_backoff_and_then_succeeds` and
   `test_errors_that_cannot_succeed_later_are_not_retried`. Explain why the
   two differ.
4. Read `test_input_tokens_alone_undercount_a_cached_request` and compute the
   total input for a request of your own.
5. Read `test_an_inference_profile_policy_also_names_each_regions_model` and
   write the policy for a profile that routes to three Regions.

## Common pitfalls

- **Expecting Bedrock to run tools.** It returns requests. Your code runs
  them, so your code must authorize them.
- **Retrying everything.** Only throttling and transient service errors can
  succeed later, and retries need a bound.
- **Summing `inputTokens` for cost or context.** It excludes cached tokens.
- **Treating a guardrail as authorization.** It filters content; it does not
  decide which actions may run.
- **Over-broad IAM.** `AmazonBedrockFullAccess` is convenient and far more
  than an agent calling one model needs.

## Further reading

- [`docs/reference/REFERENCES.md#aws-bedrock--agentcore`](../../reference/REFERENCES.md#aws-bedrock--agentcore)
- [AWS Bedrock AgentCore](aws-agentcore-tutor.md), the next course: hosting
  the agent that calls this model.

"""Amazon Bedrock at the model layer, offline, through the Agent foundations loop.

Every request and response here passes through botocore's Stubber, which
validates both against the bedrock-runtime service model, so a wrong field
name fails the test rather than a production call. Quiz questions in
evals/tutor_quizzes/aws-bedrock-tutor.jsonl cite these tests by name.
"""

import json
import random

import pytest
from botocore.exceptions import ClientError
from botocore.stub import ANY, Stubber
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.foundations.agent_loop import demo_tools, run_agent
from src.observability.telemetry import configure_telemetry
from src.runtime.bedrock_lab import (
    ConverseModel,
    apply_guardrail,
    invoke_through_profile_policy,
    stubbed_client,
    to_converse_messages,
    total_input_tokens,
    with_retries,
)

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
USAGE = {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15}


def reply(content, stop_reason, usage=USAGE):
    return {
        "output": {"message": {"role": "assistant", "content": content}},
        "stopReason": stop_reason,
        "usage": usage,
        "metrics": {"latencyMs": 1},
    }


def tool_use(tool_use_id, name, arguments):
    return {"toolUse": {"toolUseId": tool_use_id, "name": name, "input": arguments}}


@pytest.fixture
def client():
    return stubbed_client()


@pytest.fixture(scope="module")
def spans():
    exporter = InMemorySpanExporter()
    configure_telemetry().add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


def run(model, tmp_path):
    return run_agent(
        "What is the 3-year yield?",
        model,
        demo_tools(),
        allowed_tools={"interpolate_yield"},
        audit_log=tmp_path / "audit.jsonl",
    )


# --- tool use: the model asks, your code runs --------------------------------------


def test_the_agent_loop_runs_unchanged_with_bedrock_as_its_model(client, tmp_path):
    stub = Stubber(client)
    stub.add_response(
        "converse",
        reply(
            [tool_use("t1", "interpolate_yield", {"target_tenor_years": 3})], "tool_use"
        ),
        {"modelId": MODEL, "messages": ANY, "toolConfig": ANY},
    )
    # The second request must carry the tool result back in a *user* message.
    stub.add_response(
        "converse",
        reply([{"text": "The 3-year yield is 4.3%."}], "end_turn"),
        {
            "modelId": MODEL,
            "messages": [
                {"role": "user", "content": [{"text": "What is the 3-year yield?"}]},
                {
                    "role": "assistant",
                    "content": [
                        tool_use("t1", "interpolate_yield", {"target_tenor_years": 3})
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": "t1",
                                "content": [{"json": {"result": pytest.approx(4.3)}}],
                                "status": "success",
                            }
                        }
                    ],
                },
            ],
            "toolConfig": ANY,
        },
    )
    with stub:
        result = run(ConverseModel(client, MODEL), tmp_path)
    assert result.answer == "The 3-year yield is 4.3%."
    stub.assert_no_pending_responses()


def test_only_allowed_tools_are_offered_to_the_model(client, tmp_path):
    stub = Stubber(client)
    expected_tools = {
        "tools": [
            {
                "toolSpec": {
                    "name": "interpolate_yield",
                    "description": ANY,
                    "inputSchema": {"json": ANY},
                }
            }
        ]
    }
    stub.add_response(
        "converse",
        reply([{"text": "ok"}], "end_turn"),
        {"modelId": MODEL, "messages": ANY, "toolConfig": expected_tools},
    )
    with stub:
        run(ConverseModel(client, MODEL), tmp_path)


def test_a_failed_tool_goes_back_with_error_status_and_a_forbidden_one_is_refused(
    client, tmp_path
):
    stub = Stubber(client)
    stub.add_response(
        "converse",
        reply(
            [
                tool_use("t1", "interpolate_yield", {"target_tenor_years": 30}),
                tool_use("t2", "place_order", {"ticker": "X", "quantity": 1}),
            ],
            "tool_use",
        ),
    )
    stub.add_response("converse", reply([{"text": "I cannot."}], "end_turn"))
    model = ConverseModel(client, MODEL)
    with stub:
        result = run(model, tmp_path)
    # Both results go back in one user message, so the roles keep alternating.
    last_request = to_converse_messages(result.transcript[:-1])
    results = last_request[-1]["content"]
    assert last_request[-1]["role"] == "user" and len(results) == 2
    assert [r["toolResult"]["status"] for r in results] == ["error", "error"]
    assert [(r["tool_name"], r["decision"]) for r in result.audit] == [
        ("interpolate_yield", "allowed"),
        ("place_order", "denied"),
    ]


# --- errors and retries ---------------------------------------------------------------


def test_throttling_is_retried_with_backoff_and_then_succeeds(client):
    stub = Stubber(client)
    stub.add_client_error("converse", "ThrottlingException", http_status_code=429)
    stub.add_client_error("converse", "ThrottlingException", http_status_code=429)
    stub.add_response("converse", reply([{"text": "ok"}], "end_turn"))
    delays = []

    def call():
        return client.converse(
            modelId=MODEL, messages=[{"role": "user", "content": [{"text": "q"}]}]
        )

    with stub:
        response = with_retries(
            call, attempts=4, base_delay=1.0, sleep=delays.append, rng=random.Random(0)
        )
    assert response["stopReason"] == "end_turn"
    assert len(delays) == 2 and delays[0] <= 1.0 and delays[1] <= 2.0


@pytest.mark.parametrize("code", ["AccessDeniedException", "ValidationException"])
def test_errors_that_cannot_succeed_later_are_not_retried(client, code):
    stub = Stubber(client)
    stub.add_client_error("converse", code, http_status_code=400)
    delays = []
    with stub, pytest.raises(ClientError, match=code):
        with_retries(
            lambda: client.converse(
                modelId=MODEL, messages=[{"role": "user", "content": [{"text": "q"}]}]
            ),
            sleep=delays.append,
        )
    assert delays == []


def test_retries_stop_at_the_attempt_limit(client):
    stub = Stubber(client)
    for _ in range(3):
        stub.add_client_error("converse", "ThrottlingException", http_status_code=429)
    with stub, pytest.raises(ClientError, match="ThrottlingException"):
        with_retries(
            lambda: client.converse(
                modelId=MODEL, messages=[{"role": "user", "content": [{"text": "q"}]}]
            ),
            attempts=3,
            sleep=lambda _: None,
        )


def test_stubber_bypasses_botocores_own_retries():
    """Why the lab has its own retry loop: under Stubber, botocore's retry
    modes do not re-attempt a stubbed error, so their behaviour cannot be
    observed offline. In production, botocore retries throttling itself."""
    import boto3
    from botocore.config import Config

    configured = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="lab",
        aws_secret_access_key="lab",  # pragma: allowlist secret - offline stub placeholder
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )
    stub = Stubber(configured)
    stub.add_client_error("converse", "ThrottlingException", http_status_code=429)
    stub.add_response("converse", reply([{"text": "ok"}], "end_turn"))
    with stub, pytest.raises(ClientError, match="ThrottlingException"):
        configured.converse(
            modelId=MODEL, messages=[{"role": "user", "content": [{"text": "q"}]}]
        )


# --- guardrails ----------------------------------------------------------------------------


def test_a_guardrail_attached_to_converse_ends_the_turn_with_its_stop_reason(
    client, tmp_path
):
    stub = Stubber(client)
    stub.add_response(
        "converse",
        reply([{"text": "Sorry, I can't help with that."}], "guardrail_intervened"),
        {
            "modelId": MODEL,
            "messages": ANY,
            "toolConfig": ANY,
            "guardrailConfig": {"guardrailIdentifier": "gr-1", "guardrailVersion": "1"},
        },
    )
    model = ConverseModel(
        client,
        MODEL,
        guardrail={"guardrailIdentifier": "gr-1", "guardrailVersion": "1"},
    )
    with stub:
        result = run(model, tmp_path)
    assert result.answer == "Sorry, I can't help with that."
    assert model.responses[-1]["stopReason"] == "guardrail_intervened"


@pytest.mark.parametrize(
    ("action", "outputs", "expected"),
    [
        ("NONE", [], (False, "What is duration?")),
        ("GUARDRAIL_INTERVENED", [{"text": "Blocked."}], (True, "Blocked.")),
    ],
)
def test_apply_guardrail_checks_text_without_invoking_a_model(
    client, action, outputs, expected
):
    stub = Stubber(client)
    stub.add_response(
        "apply_guardrail",
        {
            "usage": {
                "topicPolicyUnits": 1,
                "contentPolicyUnits": 1,
                "wordPolicyUnits": 0,
                "sensitiveInformationPolicyUnits": 0,
                "sensitiveInformationPolicyFreeUnits": 0,
                "contextualGroundingPolicyUnits": 0,
            },
            "action": action,
            "outputs": outputs,
            "assessments": [],
        },
        {
            "guardrailIdentifier": "gr-1",
            "guardrailVersion": "1",
            "source": "INPUT",
            "content": [{"text": {"text": "What is duration?"}}],
        },
    )
    with stub:
        assert (
            apply_guardrail(client, "gr-1", "1", "What is duration?", source="INPUT")
            == expected
        )


# --- prompt caching -------------------------------------------------------------------------


def test_a_cache_point_follows_the_stable_system_prompt(client, tmp_path):
    stub = Stubber(client)
    stub.add_response(
        "converse",
        reply(
            [{"text": "ok"}],
            "end_turn",
            usage={
                "inputTokens": 12,
                "outputTokens": 4,
                "totalTokens": 1216,
                "cacheReadInputTokens": 1200,
                "cacheWriteInputTokens": 0,
            },
        ),
        {
            "modelId": MODEL,
            "messages": ANY,
            "toolConfig": ANY,
            "system": [
                {"text": "You are a rates analyst."},
                {"cachePoint": {"type": "default"}},
            ],
        },
    )
    model = ConverseModel(
        client, MODEL, system="You are a rates analyst.", cache_system=True
    )
    with stub:
        run(model, tmp_path)
    assert total_input_tokens(model.responses[-1]["usage"]) == 1212


def test_input_tokens_alone_undercount_a_cached_request():
    usage = {
        "inputTokens": 12,
        "cacheReadInputTokens": 1200,
        "cacheWriteInputTokens": 30,
    }
    assert total_input_tokens(usage) == 1242 != usage["inputTokens"]


# --- observability and least privilege -----------------------------------------------------


def test_the_chat_span_records_bedrock_usage_by_the_genai_conventions(
    client, tmp_path, spans
):
    spans.clear()
    stub = Stubber(client)
    stub.add_response("converse", reply([{"text": "ok"}], "end_turn"))
    with stub:
        result = run(ConverseModel(client, MODEL), tmp_path)
    chat = next(s for s in spans.get_finished_spans() if s.name == f"chat {MODEL}")
    assert chat.attributes["gen_ai.provider.name"] == "aws.bedrock"
    assert chat.attributes["gen_ai.usage.input_tokens"] == 10
    assert chat.attributes["gen_ai.usage.output_tokens"] == 5
    assert tuple(chat.attributes["gen_ai.response.finish_reasons"]) == ("end_turn",)
    assert f"{chat.context.trace_id:032x}" == result.trace_id


def test_an_inference_profile_policy_also_names_each_regions_model():
    profile = "arn:aws:bedrock:us-east-1:111122223333:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
    models = [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
    ]
    policy = invoke_through_profile_policy(profile, models)
    profile_stmt, model_stmt = policy["Statement"]
    assert profile_stmt["Resource"] == [profile]
    assert model_stmt["Resource"] == models
    # Models are callable only through the profile, and only for inference.
    assert (
        model_stmt["Condition"]["StringLike"]["bedrock:InferenceProfileArn"] == profile
    )
    assert {a for s in policy["Statement"] for a in s["Action"]} == {
        "bedrock:InvokeModel"
    }
    json.dumps(policy)  # serialisable as a policy document


# --- knowledge bases: retrieval versus retrieval plus generation ---------------------------


def test_retrieve_returns_chunks_and_retrieve_and_generate_returns_a_cited_answer():
    """Knowledge Bases have two query operations, and the difference is what
    comes back: Retrieve returns the matching chunks for your own prompt;
    RetrieveAndGenerate also generates the answer and returns its citations."""
    import boto3

    kb = boto3.client(
        "bedrock-agent-runtime",
        region_name="us-east-1",
        aws_access_key_id="lab",
        aws_secret_access_key="lab",  # pragma: allowlist secret - offline stub placeholder
    )
    stub = Stubber(kb)
    chunk = {"content": {"text": "Duration measures price sensitivity to rates."}}
    stub.add_response("retrieve", {"retrievalResults": [chunk]})
    stub.add_response(
        "retrieve_and_generate",
        {
            "output": {"text": "Duration measures rate sensitivity."},
            "citations": [{"retrievedReferences": [chunk]}],
            "sessionId": "s1",
        },
    )
    with stub:
        retrieved = kb.retrieve(
            knowledgeBaseId="KB12345678", retrievalQuery={"text": "What is duration?"}
        )
        generated = kb.retrieve_and_generate(
            input={"text": "What is duration?"},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": "KB12345678",
                    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
                },
            },
        )
    assert "output" not in retrieved and retrieved["retrievalResults"][0] == chunk
    assert generated["citations"][0]["retrievedReferences"][0] == chunk

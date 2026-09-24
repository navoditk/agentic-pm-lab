"""AgentCore control-plane requests, validated offline, for the AgentCore course.

Quiz questions in evals/tutor_quizzes/aws-agentcore-tutor.jsonl cite these
tests by name (`verified_by`). Every call goes through botocore's Stubber.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from botocore.exceptions import ParamValidationError
from botocore.stub import Stubber

from src.runtime.agentcore_lab import (
    LOCAL_EQUIVALENTS,
    control_client,
    memory_request,
    policy_request,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 9, 24, tzinfo=UTC)
MEMORY_ID = "desk_memory-abcdefghij"
MEMORY = {
    "memory": {
        "arn": f"arn:aws:bedrock-agentcore:us-east-1:111122223333:memory/{MEMORY_ID}",
        "id": MEMORY_ID,
        "name": "desk_memory",
        "eventExpiryDuration": 30,
        "status": "CREATING",
        "createdAt": NOW,
        "updatedAt": NOW,
    }
}
PERMIT = (
    'permit(principal, action == AgentCore::Action::"risk_metrics", '
    'resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:'
    '111122223333:gateway/desk");'
)


@pytest.fixture
def client():
    return control_client()


def test_a_memory_with_three_long_term_strategies_matches_the_service_model(client):
    request = memory_request("desk_memory")
    stub = Stubber(client)
    stub.add_response("create_memory", MEMORY, request)
    with stub:
        client.create_memory(**request)
    stub.assert_no_pending_responses()
    assert [next(iter(s)) for s in request["memoryStrategies"]] == [
        "semanticMemoryStrategy",
        "summaryMemoryStrategy",
        "userPreferenceMemoryStrategy",
    ]


def test_a_misspelled_strategy_is_rejected_before_any_call(client):
    request = memory_request("desk_memory")
    request["memoryStrategies"] = [{"semanticStrategy": {"name": "facts"}}]
    stub = Stubber(client)
    stub.add_response("create_memory", MEMORY)  # never reached
    with stub, pytest.raises(ParamValidationError, match="must be one of"):
        client.create_memory(**request)


def test_offline_validation_checks_the_minimum_expiry_but_not_the_maximum(client):
    """The model allows 3-365 days. The SDK rejects 2 locally and passes 400
    through; only the service would refuse it."""
    stub = Stubber(client)
    stub.add_response("create_memory", MEMORY)
    with stub:
        with pytest.raises(ParamValidationError, match="min value: 3"):
            client.create_memory(**memory_request("desk_memory", expiry_days=2))
        client.create_memory(**memory_request("desk_memory", expiry_days=400))
    stub.assert_no_pending_responses()  # 400 reached the (stubbed) service


def test_a_new_cedar_policy_starts_in_log_only_mode(client):
    request = policy_request("desk_engine-abcdefghij", PERMIT)
    assert request["enforcementMode"] == "LOG_ONLY"
    stub = Stubber(client)
    stub.add_response(
        "create_policy",
        {
            "policyId": "pm_desk_tools-abcdefghij",
            "name": "pm_desk_tools",
            "policyEngineId": "desk_engine-abcdefghij",
            "definition": {"cedar": {"statement": PERMIT}},
            "createdAt": NOW,
            "updatedAt": NOW,
            "policyArn": "arn:aws:bedrock-agentcore:us-east-1:111122223333:"
            "policy-engine/desk_engine-abcdefghij/policy/pm_desk_tools-abcdefghij",
            "status": "CREATING",
            "statusReasons": [],
        },
        request,
    )
    with stub:
        client.create_policy(**request)


def test_every_agentcore_service_names_a_local_equivalent_that_exists():
    assert set(LOCAL_EQUIVALENTS) == {
        "Runtime",
        "Gateway",
        "Identity",
        "Policy",
        "Memory",
        "Observability",
        "Evaluations",
    }
    for service, paths in LOCAL_EQUIVALENTS.items():
        for path in paths:
            assert (ROOT / path).exists(), f"{service}: {path} is missing"

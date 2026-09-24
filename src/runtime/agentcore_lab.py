"""AgentCore's managed services against this repository's local stack, offline.

For the AWS Bedrock AgentCore course. Each AgentCore service replaces
something this repository already does locally, and `LOCAL_EQUIVALENTS`
names it, so the course can teach every service as "what it replaces, and
what changes when it is managed".

Two control-plane requests are built here, AgentCore Memory with long-term
strategies and a Cedar policy for AgentCore Policy, and exercised through
botocore's Stubber against the `bedrock-agentcore-control` service model.
Stubber checks a request's shape, required members, and some ranges, not
everything the service enforces: the model says `eventExpiryDuration` is
3-365 days, and the SDK rejects 2 locally but passes 400 to the service.
Offline validation narrows the ways a live call can fail; it is not a
substitute for one. Each claim is pinned by a test in
tests/unit/runtime/test_agentcore_lab.py.
"""

from __future__ import annotations

from typing import Any

import boto3

# AgentCore service -> the local files that do its job in this repository.
LOCAL_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "Runtime": ("src/runtime/agentcore_app.py", "config/agentcore.yaml"),
    "Gateway": ("src/mcp_server/server.py",),
    "Identity": ("config/roles.yaml", "src/control/identity.py"),
    "Policy": (
        "governance/policies/tool-permissions.cedar",
        "governance/policies/portfolio-access.cedar",
    ),
    "Memory": ("src/context/builder.py",),
    "Observability": ("src/observability/telemetry.py",),
    "Evaluations": ("scripts/run_eval.py", "src/evals/agentcore_evaluations.py"),
}


def control_client(region: str = "us-east-1") -> Any:
    """A bedrock-agentcore-control client for Stubber: no network."""
    return boto3.client(
        "bedrock-agentcore-control",
        region_name=region,
        aws_access_key_id="lab",
        aws_secret_access_key="lab",  # pragma: allowlist secret - offline stub placeholder
    )


def memory_request(name: str, *, expiry_days: int = 30) -> dict[str, Any]:
    """A memory with short-term events kept `expiry_days`, and three
    long-term strategies, each writing to a per-actor namespace."""
    return {
        "name": name,
        "eventExpiryDuration": expiry_days,
        "memoryStrategies": [
            {
                "semanticMemoryStrategy": {
                    "name": "facts",
                    "namespaceTemplates": ["/desk/{actorId}/facts/"],
                }
            },
            {
                "summaryMemoryStrategy": {
                    "name": "session_summaries",
                    "namespaceTemplates": ["/desk/{actorId}/{sessionId}/summary/"],
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "preferences",
                    "namespaceTemplates": ["/desk/{actorId}/preferences/"],
                }
            },
        ],
    }


def policy_request(
    engine_id: str, statement: str, *, log_only: bool = True
) -> dict[str, Any]:
    """A Cedar policy for an AgentCore policy engine.

    New policies start in LOG_ONLY: the service model describes running a
    policy that way "to collect data on how it affects your application"
    before switching it to ACTIVE.
    """
    return {
        "name": "pm_desk_tools",
        "policyEngineId": engine_id,
        "definition": {"cedar": {"statement": statement}},
        "enforcementMode": "LOG_ONLY" if log_only else "ACTIVE",
    }

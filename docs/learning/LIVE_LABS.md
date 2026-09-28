# Live labs (optional)

Every course runs offline: scripted models, in-process servers, and stubbed
AWS clients. That is enough to learn every concept, and it is all that
completing a course requires. The live labs are for seeing the same code
against real services or real processes once you have done the offline lab.

Three rules hold for all of them:

- **Never required.** No course, quiz, or level depends on a live lab.
- **Never run in CI.** Nothing in `tests/` calls them; the Bedrock lab
  refuses to run when `CI` is set.
- **Stated up front.** Each lab says what it costs, which credentials it
  needs, and what to clean up, before it does anything.

| Lab | Offline lab it extends | Cost | Credentials | Cleanup |
|---|---|---|---|---|
| **MCP over real stdio**: `uv run python -m src.live_labs.mcp_stdio` | The MCP course's in-process tests (`tests/unit/mcp_server/test_client_lab.py`) | None | None; the identity is a local role name | None; the server process exits with the lab |
| **Bedrock Converse**: `uv run python -m src.live_labs.bedrock_converse --live` | The Bedrock course's Stubber tests (`tests/unit/runtime/test_bedrock_lab.py`) | At most 3 calls of up to 300 output tokens; a worst case of about one US cent at the repository's recorded rates, and the run prints its actual cost | An AWS identity with `bedrock:InvokeModel` on the inference profile and its foundation model in each Region it routes to, and model access enabled | None; nothing is created in AWS |
| **AgentCore Runtime and Gateway** | The AgentCore course's config and Stubber tests | Set a budget first; see the guides | See the guides | Required: every guide ends with teardown |

## MCP over real stdio

The MCP course connects to the server in the same process. This lab starts
`python -m src.mcp_server.server` as a separate process, as a desktop client
would, with `AGENTIC_PM_LAB_MCP_IDENTITY=PM_USER` in its environment. It
shows three things across a real process boundary:

1. The protocol negotiated over stdio (2026-07-28).
2. An unclaimed call succeeds as `PM_USER`; a call whose `_meta` claims
   `RISK_USER` is refused.
3. The server's spans join the client's trace. The server writes its spans to
   a temporary file through `AGENTIC_PM_LAB_SPAN_LOG`, and the lab prints the
   ones that share the client's trace id: the tool call, its authorization
   check, and the analytics call beneath it.

## Bedrock Converse

Run it without `--live` first. The dry run prints the model, the Region, the
exact first Converse request, and the worst-case cost, and sends nothing.

With `--live`, the lab prints the AWS account it is about to bill, then runs
the Agent foundations loop with a real model behind `ConverseModel`, allowed
one tool (`interpolate_yield`). It prints the stop reason, the tools the model
asked for, the audit decisions, the answer, the trace id, and the tokens and
cost it used. The model and Region default to the inference profile in
`config/agentcore.yaml`; override them with `--model` and `--region`.

What to look for: the model *requests* the tool and your code runs it, as in
the offline lab. If the answer differs between runs, that is the
non-determinism the Evaluations course measures with repeated trials.

## AgentCore Runtime and Gateway

These predate the live-lab convention and have their own guides:
[`AWS_AGENTCORE_SETUP.md`](../guides/AWS_AGENTCORE_SETUP.md) (account setup,
a monthly budget with alerts, a first Runtime, and teardown) and
[`AGENTCORE_GATEWAY_SETUP.md`](../guides/AGENTCORE_GATEWAY_SETUP.md). They create
real resources, so the teardown step is not optional.

# Scenario mode

Run scenarios after the learner has completed the corresponding course lesson.
First load the topic's `failure_lab` and tutor persona via `TOPIC_CATALOG`;
then ask the learner how the system should respond. Grade the answer against
the cited implementation and the course failure-lab outcome.

| Scenario | Course to resolve | Safe outcome to establish |
|---|---|---|
| A bond request omits material terms or uses stale pricing | FICC fundamentals | Abstain or require review; do not invent inputs. |
| Constraints make an allocation infeasible or concentrated | Portfolio construction | Return a constrained failure/limitation, not a plausible allocation. |
| A specialist fails after a prior stage succeeds | LangGraph and Deep Agents | Preserve completed state and use bounded retry, checkpoint, or dead-letter handling. |
| A caller requests a portfolio outside their entitlement | Governance and delivery | Deny at the authorization/tool boundary; the UI and agent intent do not authorize access. |
| Two records disagree or are unavailable at the decision time | Data provenance and research quality | Select only point-in-time eligible evidence or state uncertainty. |
| An answer passes fluency checks but lacks policy or citation support | Evaluations and AgentOps | Fail the independent policy/grounding dimension and block promotion. |
| A proposed trace includes prompts, holdings, or denied content | OpenTelemetry | Redact/minimize sensitive attributes while retaining useful correlation. |
| A Canvas action tries to bypass MCP resource checks | Copilot Canvas and MCP | Enforce identity and resource policy outside the client state. |
| A committee proposal claims certainty from incomplete evidence | Investment committee challenge | Record dissent, open questions, conditions, and approval state; never create an order. |

Award scenario XP only if the learner identifies the enforcement/recovery
layer, names the evidence boundary, and provides the expected safe outcome.

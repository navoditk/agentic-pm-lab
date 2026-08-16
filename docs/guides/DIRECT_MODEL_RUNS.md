# Direct model runs

This guide runs the institutional PM capstone against a hosted model outside
AWS. The repository records deterministic workflow stages, audit events,
OpenTelemetry token metrics, latency, approval state, and a transparent token
cost estimate. It never records a model's private chain-of-thought.

## Anthropic Messages API

Use a newly issued API key in the current shell only. Do not put a key in a
file, `.env`, experiment artifact, commit, or shell history. The key used for a
run should be revoked or rotated afterward if it was pasted into chat or any
other shared channel.

```bash
read -r -s ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY
RUN_ID="anthropic-direct-capstone-$(date -u +%Y%m%d-%H%M%S)"
RUN_DIR="experiments/runs/$RUN_ID"
uv run python scripts/experiment.py init \
  --name "Direct Anthropic institutional PM capstone" \
  --provider anthropic \
  --mode direct_messages_api \
  --model claude-haiku-4-5-20251001 \
  --run-id "$RUN_ID"
cp experiments/agentcore-runtime-proof/input.json "$RUN_DIR/input.json"

ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" uv run python scripts/run_anthropic_capstone.py \
  --output "$RUN_DIR/response.json" \
  --audit-log "$RUN_DIR/audit.jsonl" \
  --question "Assess the overnight rates and credit-risk implications for Portfolio A. Summarize evidence, assumptions, risks, and the next human review step. Do not place or recommend an order." \
  --identity PM_USER \
  --portfolio-id PORT_A \
  --decision-date 2026-08-13 \
  --request-id "$RUN_ID"

uv run python scripts/experiment.py record \
  --run-dir "$RUN_DIR" \
  --status success \
  --usage-json "$RUN_DIR/response.json" \
  --input-rate 1.00 \
  --output-rate 5.00 \
  --pricing-source "Anthropic direct API pricing" \
  --pricing-as-of 2026-08-16 \
  --latency-ms "$(jq -r .latency_ms "$RUN_DIR/response.json" | awk '{printf "%d", $1}')" \
  --input-path input.json \
  --output-path response.json \
  --evidence "response.json,audit.jsonl"

uv run python scripts/experiment.py finalize \
  --run-dir "$RUN_DIR" \
  --status success \
  --decision "Claude summary completed; human approval remains required and no order was executed." \
  --cleanup-status not_required \
  --cleanup-note "Direct API run has no provisioned cloud resources."
unset ANTHROPIC_API_KEY
```

The model adapter is [`scripts/run_anthropic_capstone.py`](../../scripts/run_anthropic_capstone.py).
The completed reference run is
[`experiments/runs/anthropic-direct-capstone-20260816-230000/`](../../experiments/runs/anthropic-direct-capstone-20260816-230000/).
Its fixture data is public/mock learning data, not investment advice. The
recorded reference result used 613 input tokens, 300 output tokens, 3,706 ms,
and an estimated `$0.002113` token cost. Provider billing is authoritative.

## Safety and interpretation

- The deterministic capstone performs the portfolio, research, challenge, and
  approval checks before narration. The model does not authorize tools or place
  orders.
- `approval_required: true` and `order_execution: false` are required outcomes
  for this exercise.
- Token counts come from the provider response. Cost is estimated from the
  rates captured in the run manifest and excludes any unrelated account costs.
- A response stopping at `max_tokens` is a quality signal to review, not proof
  that the summary is complete.
- Direct hosted runs are optional. The fixture runner remains the zero-cost,
  offline path for learners and unit tests.

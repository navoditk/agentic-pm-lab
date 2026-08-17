import pytest

from scripts.run_agentcore_benchmark import invoke_runtime, wait_for_status


def test_wait_for_status_returns_when_resource_is_ready():
    statuses = iter(["CREATING", "READY"])

    assert (
        wait_for_status(lambda: next(statuses), attempts=2, delay_seconds=0) == "READY"
    )


def test_wait_for_status_fails_fast_on_terminal_failure():
    with pytest.raises(RuntimeError, match="failure state"):
        wait_for_status(lambda: "FAILED", attempts=2, delay_seconds=0)


def test_invoke_runtime_retries_initialization_timeout():
    class Body:
        def read(self):
            return b'{"usage": {"totalTokens": 1}}'

        def close(self):
            pass

    class Client:
        calls = 0

        def invoke_agent_runtime(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("Runtime initialization time exceeded")
            return {"response": Body()}

    raw, session_id, latency_ms = invoke_runtime(
        Client(),
        "arn:aws:example",
        {"question": "test"},
        attempts=2,
        retry_delay_seconds=0,
    )

    assert raw == b'{"usage": {"totalTokens": 1}}'
    assert session_id.startswith("canonical-")
    assert latency_ms >= 0

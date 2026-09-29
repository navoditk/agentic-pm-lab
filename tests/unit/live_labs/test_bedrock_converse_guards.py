"""The live Bedrock lab's guards, tested offline.

The live run itself is never exercised here or in CI. These tests pin what
keeps it safe: a dry run by default, a refusal under CI, and a bounded
request. boto3.client is replaced so that creating any client fails.
"""

import pytest

from src.live_labs import bedrock_converse as lab


@pytest.fixture(autouse=True)
def no_aws(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a live-lab test tried to create an AWS client")

    monkeypatch.setattr("boto3.client", refuse)


def test_the_default_is_a_dry_run_that_sends_nothing(capsys, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    assert lab.main([]) == 0
    out = capsys.readouterr().out
    assert "Dry run: nothing is sent to AWS." in out
    assert '"maxTokens": 300' in out


def test_live_runs_are_refused_in_ci(capsys, monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert lab.main(["--live"]) == 2
    assert "never run in CI" in capsys.readouterr().err


def test_the_request_offers_one_tool_and_caps_output():
    request = lab.first_request(lab.MODEL)
    assert [t["toolSpec"]["name"] for t in request["toolConfig"]["tools"]] == [
        "interpolate_yield"
    ]
    assert request["inferenceConfig"] == {"maxTokens": lab.MAX_TOKENS}


def test_the_worst_case_uses_the_repository_rates():
    # 3 calls x (2,000 input at $1/M + 300 output at $5/M)
    assert lab.worst_case_usd(lab.MODEL) == pytest.approx(0.0105)

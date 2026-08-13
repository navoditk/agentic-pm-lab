import json

from scripts.experiment import main


def test_init_record_and_check_run(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "experiment",
            "init",
            "--name",
            "local smoke",
            "--provider",
            "local",
            "--model",
            "mock-1",
            "--run-id",
            "smoke",
            "--output-dir",
            str(tmp_path / "runs"),
        ],
    )
    assert main() == 0
    run_dir = tmp_path / "runs" / "smoke"
    monkeypatch.setattr(
        "sys.argv",
        [
            "experiment",
            "record",
            "--run-dir",
            str(run_dir),
            "--status",
            "success",
            "--input-tokens",
            "1000",
            "--output-tokens",
            "500",
            "--input-rate",
            "1",
            "--output-rate",
            "2",
            "--latency-ms",
            "42",
        ],
    )
    assert main() == 0
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["usage"]["total_tokens"] == 1500
    assert manifest["costs"]["token_estimate_usd"] == 0.002

    usage_path = tmp_path / "provider-response.json"
    usage_path.write_text(
        json.dumps({"usage": {"prompt_tokens": 7, "completion_tokens": 3}})
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "experiment",
            "record",
            "--run-dir",
            str(run_dir),
            "--usage-json",
            str(usage_path),
        ],
    )
    assert main() == 0
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["usage"]["input_tokens"] == 7
    assert manifest["usage"]["output_tokens"] == 3

    monkeypatch.setattr(
        "sys.argv",
        [
            "experiment",
            "record",
            "--run-dir",
            str(run_dir),
            "--aws-estimated",
            "0.5",
            "--aws-observed",
            "0.2",
        ],
    )
    assert main() == 0
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["costs"]["total_estimated_usd"] == 0.200013

    monkeypatch.setattr("sys.argv", ["experiment", "check", "--run-dir", str(run_dir)])
    assert main() == 0
    assert '"status": "success"' in capsys.readouterr().out

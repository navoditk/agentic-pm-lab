from pathlib import Path

from fastapi.testclient import TestClient

from scripts import artifacts_host


def test_risk_summary_artifact_is_single_file_and_labels_provenance(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(artifacts_host, "ARTIFACTS_DIR", tmp_path)
    client = TestClient(artifacts_host.app)

    response = client.post("/generate/risk-summary")

    assert response.status_code == 200
    payload = response.json()
    report = (tmp_path / payload["filename"]).read_text()
    assert "not investment advice" in report
    assert "mock holdings" in report

from urllib.error import URLError

from scripts.monitor_curriculum_sources import (
    build_report,
    monitor_source,
    write_issue_files,
)


def test_pypi_source_reports_changed_version():
    source = {
        "id": "sample",
        "title": "Sample",
        "url": "https://example.com",
        "kind": "pypi",
        "version_or_fingerprint": "1.0.0",
        "impacts": [{"topic": "ficc-tutor-agent", "assets": ["example.md"]}],
    }

    result = monitor_source(
        source,
        fetch=lambda _url, _method: ({}, b'{"info": {"version": "2.0.0"}}'),
    )

    assert result["status"] == "changed"
    assert result["observed"] == "2.0.0"


def test_url_source_requires_initial_monitor_baseline():
    source = {
        "id": "sample",
        "title": "Sample",
        "url": "https://example.com",
        "kind": "url",
        "version_or_fingerprint": "documentation-reviewed",
        "impacts": [{"topic": "ficc-tutor-agent", "assets": ["example.md"]}],
    }

    result = monitor_source(
        source, fetch=lambda _url, _method: ({"etag": '"abc"'}, b"")
    )

    assert result["status"] == "unbaselined"
    assert result["observed"] == '"abc"'


def test_unavailable_source_is_reported_without_failure():
    source = {
        "id": "sample",
        "title": "Sample",
        "url": "https://example.com",
        "kind": "url",
        "version_or_fingerprint": "documentation-reviewed",
        "impacts": [{"topic": "ficc-tutor-agent", "assets": ["example.md"]}],
    }

    result = monitor_source(
        source, fetch=lambda _url, _method: (_ for _ in ()).throw(URLError("offline"))
    )

    assert result["status"] == "unavailable"


def test_report_and_issue_files_include_only_actionable_sources(tmp_path):
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        """version: 1
sources:
  - id: sample
    title: Sample
    url: https://example.com
    kind: pypi
    version_or_fingerprint: "1.0.0"
    impacts:
      - topic: ficc-tutor-agent
        assets: [example.md]
"""
    )
    report = build_report(
        registry, fetch=lambda _url, _method: ({}, b'{"info": {"version": "2.0.0"}}')
    )
    issue_dir = tmp_path / "issues"
    write_issue_files(report, issue_dir)

    assert report["summary"]["changed"] == 1
    assert (
        (issue_dir / "sample.md")
        .read_text()
        .startswith("## External curriculum source review")
    )

from src.control.audit import read_audit_log, record_audit_event


def test_record_audit_event_returns_the_written_record(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    record = record_audit_event("pm_user", "pm", "price-bond", True, log_path=log_path)
    assert record["identity"] == "pm_user"
    assert record["role"] == "pm"
    assert record["tool_name"] == "price-bond"
    assert record["allowed"] is True
    assert "timestamp" in record


def test_read_audit_log_returns_empty_list_when_file_missing(tmp_path):
    missing_path = tmp_path / "does_not_exist.jsonl"
    assert read_audit_log(log_path=missing_path) == []


def test_audit_log_is_append_only_and_ordered(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    record_audit_event("pm_user", "pm", "curve", True, log_path=log_path)
    record_audit_event("risk_user", "risk", "price-bond", False, log_path=log_path)

    records = read_audit_log(log_path=log_path)

    assert len(records) == 2
    assert records[0]["tool_name"] == "curve"
    assert records[0]["allowed"] is True
    assert records[1]["tool_name"] == "price-bond"
    assert records[1]["allowed"] is False

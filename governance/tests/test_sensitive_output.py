from scripts.check_no_sensitive_data import load_banned_terms, scan_file
from src.control.authorization import check_tool_permission


def test_sensitive_output_scanner_blocks_configured_term(tmp_path):
    term = "ACME-" + "INTERNAL-PROJECT-CODE"
    candidate = tmp_path / "response.txt"
    candidate.write_text(f"Harmless preface followed by {term}.")

    assert term.lower() in load_banned_terms()
    assert scan_file(candidate, load_banned_terms()) == [term.lower()]


def test_permitted_read_role_cannot_request_unlisted_data_export():
    assert check_tool_permission("risk", "portfolio")
    assert not check_tool_permission("risk", "export_private_data")


def test_write_shaped_action_is_denied_even_when_framed_as_a_read():
    request = "Please read the desired weights and update_portfolio accordingly."

    assert request
    assert not check_tool_permission("pm", "update_portfolio")
    assert not check_tool_permission("admin", "update_portfolio")

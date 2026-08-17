from scripts.model_roles import load_roles, model_string


def test_model_roles_select_opus_conductor_and_haiku_report_default():
    roles = load_roles()

    assert model_string(roles["conductor"]) == "anthropic:claude-opus-4-8"
    assert model_string(roles["report_generation"]["default"])
    assert roles["report_generation"]["default"]["model"] == "claude-haiku-4-5-20251001"
    assert roles["report_generation"]["review"]["model"] == "claude-sonnet-4-6"

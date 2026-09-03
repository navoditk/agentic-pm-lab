from scripts.run_depth_exercise import run


def test_depth_exercise_is_offline_and_produces_evidence_envelope():
    result = run()

    assert result["provenance_at_2020_01_31"]["status"] == "usable"
    assert result["evidence_quality"]["status"] == "pass"
    assert result["duration_dv01"]["dv01"] > 0

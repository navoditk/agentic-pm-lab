from scripts.check_tutor_courses import check, check_learning_order


def test_all_tutor_topics_have_complete_offline_courses():
    assert check() == []


def _courses(*rows, required=True):
    return {
        topic: {"step": step, "stage": stage, "required": required}
        for topic, step, stage in rows
    }


def test_a_well_formed_order_passes():
    courses = _courses(("a", 1, "One"), ("b", 2, "One"), ("c", 3, "Two"))
    assert check_learning_order(["a", "b", "c"], courses) == []


def test_a_gap_in_steps_is_reported():
    courses = _courses(("a", 1, "One"), ("b", 3, "One"))
    assert any("no gaps" in e for e in check_learning_order(["a", "b"], courses))


def test_catalog_order_must_follow_steps():
    """Everything that iterates TOPIC_CATALOG inherits its order from it."""
    courses = _courses(("a", 2, "One"), ("b", 1, "One"))
    errors = check_learning_order(["a", "b"], courses)
    assert any("TOPIC_CATALOG order" in e for e in errors)


def test_a_stage_split_by_another_stage_is_reported():
    """Otherwise the CLI would print the same stage heading twice."""
    courses = _courses(("a", 1, "One"), ("b", 2, "Two"), ("c", 3, "One"))
    errors = check_learning_order(["a", "b", "c"], courses)
    assert any("split" in e for e in errors)


def test_a_non_integer_step_is_reported_without_crashing():
    courses = {"a": {"step": "1", "stage": "One"}}
    assert check_learning_order(["a"], courses) == ["a: step must be an integer"]


def test_a_module_is_required_or_optional_as_a_whole():
    """A half-required module would make "skip this module" meaningless."""
    courses = _courses(("a", 1, "Core"), ("b", 2, "Core"))
    courses["b"]["required"] = False
    errors = check_learning_order(["a", "b"], courses)
    assert any("required setting" in e for e in errors)

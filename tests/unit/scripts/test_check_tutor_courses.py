from scripts.check_tutor_courses import check


def test_all_tutor_topics_have_complete_offline_courses():
    assert check() == []

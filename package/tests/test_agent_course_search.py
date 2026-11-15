from types import SimpleNamespace
from tue_api_wrapper.moodle_models import MoodleCourseSummary

from tue_api_wrapper.agent_course_search import search_courses_live


def test_live_search_preserves_separate_sources_and_pagination():
    client = SimpleNamespace(
        alma=SimpleNamespace(course_offerings=lambda **kwargs: SimpleNamespace(results=[{"title": "Algorithms"}], selected_term_label="Winter")),
        ilias=SimpleNamespace(search=lambda *args, **kwargs: SimpleNamespace(results=[{"title": "Algorithms WS"}], next_page_url="next")),
        moodle=SimpleNamespace(search_courses=lambda *args, **kwargs: SimpleNamespace(items=[MoodleCourseSummary(1, "Algorithms", "ALG", None, True, None, "https://moodle/course", None)], next_page=1, source_url="https://moodle/course/search.php")),
    )
    result = search_courses_live(client, "Algorithms", limit=10)
    assert result["sources"]["alma"]["items"][0]["title"] == "Algorithms"
    assert result["sources"]["ilias"]["has_next_page"] is True
    assert result["sources"]["moodle"]["next_offset"] == 10
    assert result["sources"]["moodle"]["scope"] == "visible_catalogue"
    assert result["matches"] == "candidates_only"


def test_live_search_reports_source_failure_without_hiding_other_results():
    def fail(*args, **kwargs):
        raise TimeoutError("network")
    client = SimpleNamespace(alma=SimpleNamespace(course_offerings=fail),
        ilias=SimpleNamespace(search=lambda *a, **kw: SimpleNamespace(results=[], next_page_url=None)),
        moodle=SimpleNamespace(search_courses=lambda *args, **kw: SimpleNamespace(items=[], next_page=None, source_url="https://moodle/course/search.php")))
    result = search_courses_live(client, "Algorithms")
    assert result["sources"]["alma"]["status"] == "error"
    assert result["sources"]["ilias"]["status"] == "ok"

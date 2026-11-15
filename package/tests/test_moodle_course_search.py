from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_course_search import search_moodle_courses, raw_moodle_course_search


def test_catalog_search_uses_server_query_and_preserves_pagination():
    html = '''<div id="page-course-search"><div class="course-search-result">
    <div class="coursebox" data-courseid="42"><h3 class="coursename"><a href="/course/view.php?id=42">Machine Learning</a></h3></div>
    <a href="/course/search.php?search=Machine&amp;page=1&amp;perpage=10">2</a></div></div>'''
    session = Mock()
    session.get.return_value = SimpleNamespace(text=html, url="https://moodle.zdv.uni-tuebingen.de/course/search.php?search=Machine&page=0", status_code=200, raise_for_status=lambda: None)
    client = SimpleNamespace(base_url="https://moodle.zdv.uni-tuebingen.de", session=session, timeout_seconds=10)
    result = search_moodle_courses(client, "Machine", page=0, per_page=10)
    assert result.items[0].title == "Machine Learning"
    assert result.next_page == 1
    assert session.get.call_args.kwargs["params"] == {"search": "Machine", "page": 0, "perpage": 10}


def test_unexpected_page_is_not_an_empty_search_result():
    session = Mock()
    session.get.return_value = SimpleNamespace(text="<h1>Maintenance</h1>", url="https://moodle.zdv.uni-tuebingen.de/course/search.php", status_code=200, raise_for_status=lambda: None)
    with pytest.raises(AlmaParseError):
        search_moodle_courses(SimpleNamespace(base_url="https://moodle.zdv.uni-tuebingen.de", session=session, timeout_seconds=10), "Machine")


def test_raw_search_returns_unparsed_response():
    session = Mock()
    session.get.return_value = SimpleNamespace(text="<h1>changed</h1>", url="https://moodle.zdv.uni-tuebingen.de/course/search.php", status_code=200, headers={}, raise_for_status=lambda: None)
    client = SimpleNamespace(base_url="https://moodle.zdv.uni-tuebingen.de", session=session, timeout_seconds=10)
    assert raw_moodle_course_search(client, "Machine")["body"] == "<h1>changed</h1>"


def test_unknown_empty_markup_is_not_claimed_as_no_results():
    session = Mock()
    session.get.return_value = SimpleNamespace(text='<div class="course-search-result"><div>new course layout</div></div>', url="https://moodle.zdv.uni-tuebingen.de/course/search.php", status_code=200, raise_for_status=lambda: None)
    with pytest.raises(AlmaParseError):
        search_moodle_courses(SimpleNamespace(base_url="https://moodle.zdv.uni-tuebingen.de", session=session, timeout_seconds=10), "Machine")


def test_explicit_no_courses_message_is_an_empty_result():
    session = Mock()
    session.get.return_value = SimpleNamespace(text='<h2>No courses were found with the words Machine</h2>', url="https://moodle.zdv.uni-tuebingen.de/course/search.php", status_code=200, raise_for_status=lambda: None)
    result = search_moodle_courses(SimpleNamespace(base_url="https://moodle.zdv.uni-tuebingen.de", session=session, timeout_seconds=10), "Machine")
    assert result.items == ()

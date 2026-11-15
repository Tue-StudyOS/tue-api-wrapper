from types import SimpleNamespace
from unittest.mock import Mock

from tue_api_wrapper.alma_course_search_raw import fetch_raw_alma_search
import pytest
from tue_api_wrapper.config import AlmaParseError

FORM = '''<h1>Veranstaltungen suchen</h1><form id="genericSearchMask" action="/alma/search">
<input name="genericSearchMask:query" type="text" placeholder="Nummer, Titel, Dozent" />
<select name="genericSearchMask:termSelect_input"><option value="eq|30|2026">Sommersemester 2026</option></select>
<button name="genericSearchMask:buttonsBottom:search">Suchen</button></form>'''


def test_raw_search_returns_unparsed_server_result(monkeypatch):
    monkeypatch.setattr("tue_api_wrapper.alma_course_search_raw.COURSE_SEARCH_URL", "https://alma.example/alma/search")
    session = Mock()
    session.get.return_value = SimpleNamespace(text=FORM, url="https://alma.example/alma/search", status_code=200, headers={}, raise_for_status=lambda: None)
    session.post.return_value = SimpleNamespace(text="<div>new layout not parsed</div>", url="https://alma.example/alma/search", status_code=200, headers={}, raise_for_status=lambda: None)
    response = fetch_raw_alma_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    assert response["body"] == "<div>new layout not parsed</div>"
    assert session.post.call_count == 1


def test_raw_form_does_not_parse_or_post(monkeypatch):
    monkeypatch.setattr("tue_api_wrapper.alma_course_search_raw.COURSE_SEARCH_URL", "https://alma.example/alma/search")
    session = Mock()
    session.get.return_value = SimpleNamespace(text="<form>changed layout</form>", url="https://alma.example/alma/search", status_code=200, headers={}, raise_for_status=lambda: None)
    response = fetch_raw_alma_search(SimpleNamespace(session=session, timeout_seconds=10), form_only=True)
    assert response["body"] == "<form>changed layout</form>"
    session.post.assert_not_called()


def test_raw_results_follow_same_alma_search_flow_redirect(monkeypatch):
    monkeypatch.setattr("tue_api_wrapper.alma_course_search_raw.COURSE_SEARCH_URL", "https://alma.example/alma/search")
    session = Mock()
    initial = SimpleNamespace(text=FORM, url="https://alma.example/alma/search", status_code=200, headers={}, raise_for_status=lambda: None)
    final = SimpleNamespace(text="<html>actual results</html>", url="https://alma.example/alma/search?_flowId=course", status_code=200, headers={})
    session.get.side_effect = [initial, final]
    session.post.return_value = SimpleNamespace(text="", url="https://alma.example/alma/search?_flowId=course", status_code=302, headers={"Location": "/alma/search?_flowId=course&_flowExecutionKey=next"})
    result = fetch_raw_alma_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    assert result["body"] == "<html>actual results</html>"
    assert session.get.call_args.kwargs["allow_redirects"] is False


def test_raw_results_reject_cross_host_redirect(monkeypatch):
    monkeypatch.setattr("tue_api_wrapper.alma_course_search_raw.COURSE_SEARCH_URL", "https://alma.example/alma/search")
    session = Mock()
    session.get.return_value = SimpleNamespace(text=FORM, url="https://alma.example/alma/search", status_code=200, headers={}, raise_for_status=lambda: None)
    session.post.return_value = SimpleNamespace(text="", url="https://alma.example/alma/search?_flowId=course", status_code=302, headers={"Location": "https://evil.example/alma/search?_flowId=course"})
    with pytest.raises(AlmaParseError):
        fetch_raw_alma_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    assert session.get.call_count == 1

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tue_api_wrapper.alma_course_search_client import search_courses
from tue_api_wrapper.config import AlmaParseError

FORM = '''<h1>Veranstaltungen suchen</h1><form id="genericSearchMask" action="/search">
<input name="genericSearchMask:query" type="text" placeholder="Nummer, Titel, Dozent" />
<select name="genericSearchMask:termSelect_input">
<option value="eq|31|2026" selected>Wintersemester 2026</option>
<option value="eq|30|2026">Sommersemester 2026</option></select>
<button name="genericSearchMask:buttonsBottom:search">Suchen</button></form>'''


def client_with_response(html=FORM):
    session = Mock()
    session.get.return_value = SimpleNamespace(text=FORM, url="https://alma.example/search", raise_for_status=lambda: None)
    session.post.return_value = SimpleNamespace(text=html, url="https://alma.example/search", raise_for_status=lambda: None)
    return SimpleNamespace(session=session, timeout_seconds=10)


def test_invalid_period_id_is_rejected_before_search():
    client = client_with_response()
    with pytest.raises(AlmaParseError, match="search term"):
        search_courses(client, query="Advanced Information Retrieval", term="237")
    client.session.post.assert_not_called()


def test_term_only_search_submits_selected_term():
    client = client_with_response()
    page = search_courses(client, term="eq|30|2026")
    client.session.post.assert_called_once()
    assert client.session.post.call_args.kwargs["data"]["genericSearchMask:termSelect_input"] == "eq|30|2026"
    assert page.selected_term_value == "eq|30|2026"


def test_validation_error_is_not_reported_as_empty_results():
    client = client_with_response(FORM + '<div class="ui-messages-error">Keine gültige Auswahl.</div>')
    with pytest.raises(AlmaParseError, match="rejected"):
        search_courses(client, query="Advanced Information Retrieval")


def test_unexpected_response_is_not_reported_as_empty_results():
    client = client_with_response('<h1>Maintenance</h1>')
    with pytest.raises(AlmaParseError):
        search_courses(client, query="Advanced Information Retrieval")


def test_successful_result_page_does_not_require_search_form():
    client = client_with_response('''<table id="genSearchRes:abcTable"><tr>
<td><a href="/detail">Details</a></td><td>INFO4275</td>
<td>Advanced Information Retrieval</td><td>Lecture</td><td></td><td></td><td>Informatik</td><td></td>
</tr></table>''')
    page = search_courses(client, query="Advanced Information Retrieval")
    assert page.results[0].number == "INFO4275"

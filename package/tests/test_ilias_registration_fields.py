from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_actions_client import join_course
from tue_api_wrapper.ilias_actions_html import parse_course_join_result

URL = 'https://ovidius.uni-tuebingen.de/ilias.php?cmdClass=ilCourseRegistrationGUI&rtoken=private'
INITIAL = f'<form action="{URL}"><input name="cmd[join]" type="submit" value="Beitreten"></form>'
DETAILS = f'''<form action="{URL}">
<input name="cdf_8073" id="semester"><label for="semester">Fachsemester</label>
<select name="cdf_8074"><option value="">Auswahl</option><option value="8074_1">Informatik</option></select>
<select name="cdf_8075"><option value="">Auswahl</option><option value="8075_1">Master</option></select>
<input type="checkbox" name="agreement"><input type="submit" name="cmd[join]" value="Beitreten"></form>'''
DONE = '<p>Sie sind dem Kurs beigetreten.</p>'
VALUES = {'cdf_8073': '3', 'cdf_8074': '8074_1', 'cdf_8075': '8075_1'}


def response(html):
    return SimpleNamespace(text=html, url=URL, raise_for_status=lambda: None)


def client():
    session = Mock()
    session.get.return_value = response(INITIAL)
    session.post.side_effect = [response(DETAILS), response(DONE)]
    return SimpleNamespace(session=session, timeout_seconds=10)


def test_second_step_reports_required_fields_without_claiming_join():
    api = client()
    result = join_course(api, url=URL, accept_agreement=True)
    assert result.status == 'requires_input'
    assert len(result.registration_fields) == 3
    assert 'rtoken' not in result.final_url
    assert api.session.post.call_count == 1


def test_second_step_posts_explicit_validated_values():
    api = client()
    result = join_course(api, url=URL, accept_agreement=True, registration_values=VALUES)
    assert result.status == 'joined'
    payload = api.session.post.call_args.kwargs['data']
    assert all(payload[key] == value for key, value in VALUES.items())
    assert payload['agreement'] == '1'
    assert api.session.post.call_count == 2


def test_invalid_selection_stops_before_second_post():
    api = client()
    with pytest.raises(AlmaParseError, match='Invalid selection'):
        join_course(api, url=URL, accept_agreement=True, registration_values=VALUES | {'cdf_8075': 'invented'})
    assert api.session.post.call_count == 1


def test_unrelated_membership_text_does_not_prove_join():
    result = parse_course_join_result('<p>Mitgliedschaft beantragen</p>', URL)
    assert result.status != 'joined'


def test_api_route_forwards_registration_body():
    from unittest.mock import patch
    from tue_api_wrapper import api_routes_edit_actions as routes
    result = parse_course_join_result(DONE, URL)
    with patch.object(routes.portal_service, '_ilias_client', return_value=object()), patch.object(
        routes.portal_service, 'invalidate_portal_cache'
    ), patch.object(routes, 'join_course', return_value=result) as join:
        data = routes.ilias_course_join(url=URL, accept_agreement=True, registration_values=VALUES)
    assert join.call_args.kwargs['registration_values'] == VALUES
    assert data['status'] == 'joined'

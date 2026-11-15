import json
from types import SimpleNamespace

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_course_content import parse_course_content
from tue_api_wrapper import study_radar_cli, mcp_study


HTML = '''<main><div class="course-content"><ul>
<li id="section-0" class="section course-section"><h3 class="sectionname">General</h3><div class="summary">Read the syllabus.</div>
<li id="module-7" class="activity modtype_label"><div class="activity-altcontent">
Course details <a href="https://alma.uni-tuebingen.de/alma/pages/startFlow.xhtml?_flowId=detailView-flow&amp;unitId=12">Alma listing</a>
<a href="https://ovidius.uni-tuebingen.de/goto.php/crs/42">ILIAS room</a></div></li>
<li id="module-8" class="activity modtype_forum"><div class="activityname"><a href="/mod/forum/view.php?id=8">Announcements</a></div></li>
</li><li id="section-1" class="section course-section"><h3 class="sectionname">Week 1</h3></li>
</ul></div></main>'''
URL = 'https://moodle.zdv.uni-tuebingen.de/course/view.php?id=1'


def test_course_content_preserves_sections_activities_and_cross_system_evidence():
    result = parse_course_content(HTML, URL, 1)
    assert [s.title for s in result.sections] == ['General', 'Week 1']
    assert result.sections[0].description == 'Read the syllabus.'
    assert result.sections[0].activities[1].kind == 'forum'
    assert result.sections[0].activities[1].url.endswith('/mod/forum/view.php?id=8')
    assert [(link.service, link.label, link.section_id, link.activity_id) for link in result.cross_system_links] == [
        ('alma', 'Alma listing', 'section-0', 'module-7'), ('ilias', 'ILIAS room', 'section-0', 'module-7')]
    assert result.coverage == 'visible_course_page'


def test_university_hostname_must_match_exactly():
    html = HTML.replace('alma.uni-tuebingen.de', 'alma.uni-tuebingen.de.example.com')
    result = parse_course_content(html, URL, 1)
    assert [link.service for link in result.cross_system_links] == ['ilias']


def test_unrecognized_or_enrollment_page_is_not_empty_course():
    with pytest.raises(AlmaParseError):
        parse_course_content('<html>Not enrolled</html>', URL, 1)


def test_cli_and_mcp_expose_course_content(monkeypatch, capsys):
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    client = SimpleNamespace(moodle=SimpleNamespace(course_content=lambda course_id: {'course_id': course_id}), close=lambda: None)
    monkeypatch.setattr(study_radar_cli, 'make_client', lambda _: (client, 'student'))
    monkeypatch.setattr(mcp_study, 'make_client', lambda _: (client, 'student'))
    assert study_radar_cli.main(['moodle-content', '--target', '42']) == 0
    assert json.loads(capsys.readouterr().out)['course_id'] == 42
    register = mcp_study.register_study_tools
    register(Server(), None)
    assert tools['study_moodle_content'](42)['course_id'] == 42

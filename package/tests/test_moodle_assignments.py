import json
from types import SimpleNamespace

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_assignment import parse_assignment
from tue_api_wrapper import mcp_study, study_radar_cli


URL = 'https://moodle.zdv.uni-tuebingen.de/mod/assign/view.php?id=25'
HTML = '''<div id="page-header"><h1>Exercise</h1></div><div id="region-main">
<div id="intro" class="activity-description"><p>Explain your answer.</p><a href="/pluginfile.php/1/sheet.pdf">Sheet</a></div>
<div class="submissionstatustable"><h3>Submission status</h3><table><tr><th>Submission status</th><td>Draft</td></tr>
<tr><th>File submissions</th><td><a href="/pluginfile.php/2/answer.pdf">answer.pdf</a></td></tr></table></div>
<div class="feedback"><h3>Feedback</h3><table><tr><th>Grade</th><td>8 / 10</td></tr>
<tr><th>Feedback comments</th><td>Good work</td></tr></table></div>
<div class="singlebutton"><form method="get" action="/mod/assign/view.php"><input type="hidden" name="id" value="25">
<input type="hidden" name="action" value="editsubmission"><button>Edit submission</button></form></div>
</div>'''


def test_assignment_details_include_instructions_submission_feedback_and_actions():
    a = parse_assignment(HTML, URL, 25)
    assert a.title == 'Exercise'
    assert 'Explain your answer.' in a.instructions
    assert a.instruction_links[0].label == 'Sheet'
    assert a.submission[0].label == 'Submission status'
    assert a.submission[0].value == 'Draft'
    assert a.submission[1].links[0].label == 'answer.pdf'
    assert a.feedback[1].value == 'Good work'
    assert a.available_actions == ('editsubmission',)


def test_assignment_rejects_unrecognized_page():
    with pytest.raises(AlmaParseError):
        parse_assignment('<html>access denied</html>', URL, 25)


def test_assignment_cli_and_mcp(monkeypatch, capsys):
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    client = SimpleNamespace(moodle=SimpleNamespace(assignment=lambda assignment_id: {'assignment_id': assignment_id}), close=lambda: None)
    monkeypatch.setattr(study_radar_cli, 'make_client', lambda _: (client, 'student'))
    monkeypatch.setattr(mcp_study, 'make_client', lambda _: (client, 'student'))
    assert study_radar_cli.main(['moodle-assignment', '--target', '25']) == 0
    assert json.loads(capsys.readouterr().out)['assignment_id'] == 25
    mcp_study.register_study_tools(Server(), None)
    assert tools['study_moodle_assignment'](25)['assignment_id'] == 25


def test_submission_form_inspection_redacts_tokens_and_finds_limits():
    from tue_api_wrapper.moodle_submission import inspect_submission_form
    html = '''<form method="post" action="/mod/assign/view.php"><input type="hidden" name="id" value="25">
    <input type="hidden" name="action" value="savesubmission"><input type="hidden" name="sesskey" value="secret">
    <input type="hidden" name="files_filemanager" value="123"></form>
    <script>M.form_filemanager.init(Y, {"itemid":123,"maxfiles":2,"maxbytes":2048,"filecount":0,
      "accepted_types":[".pdf"],"filepicker":{"repositories":{"5":{"type":"upload"}}}});</script>'''
    result = inspect_submission_form(html, URL, 25)
    assert result['file_manager']['max_files'] == 2
    assert result['file_manager']['accepted_types'] == ['.pdf']
    assert result['file_manager']['upload_available'] is True
    assert 'secret' not in json.dumps(result)


def test_submission_inspection_refuses_missing_or_wrong_form():
    from tue_api_wrapper.moodle_submission import inspect_submission_form
    with pytest.raises(AlmaParseError):
        inspect_submission_form('<form action="https://evil.example/" method="post"></form>', URL, 25)

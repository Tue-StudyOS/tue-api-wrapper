from types import SimpleNamespace

import pytest

from tue_api_wrapper.moodle_submission_actions import classify_receipt, validate_upload_response
from tue_api_wrapper.config import AlmaParseError


def test_receipt_requires_positive_status_and_matching_bytes():
    fields = [SimpleNamespace(label='Abgabestatus', value='Zur Bewertung abgegeben', links=())]
    assert classify_receipt(fields, True) == 'submitted'
    assert classify_receipt(fields, False) == 'unknown'
    fields[0].value = 'Entwurf (nicht abgegeben)'
    assert classify_receipt(fields, True) == 'draft'
    fields[0].value = 'unknown'
    assert classify_receipt(fields, True) == 'unknown'


def test_upload_receipt_must_match_file_and_not_indicate_conflict():
    assert validate_upload_response({'file': 'work.pdf', 'id': 3}, 'work.pdf', '3') is None
    for result in ({'event': 'fileexists'}, {'error': 'denied'}, {'file': 'other.pdf'}, {}):
        with pytest.raises(AlmaParseError):
            validate_upload_response(result, 'work.pdf', '3')


class Response:
    def __init__(self, url, text='', status=200, data=None, content=b''):
        self.url, self.text, self.status_code, self.data, self.content = url, text, status, data, content
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP error')
    def json(self):
        return self.data
    def iter_content(self, size):
        yield self.content
    def close(self):
        pass


class FakeMoodle:
    base_url = 'https://moodle.example'
    timeout_seconds = 5
    def __init__(self):
        self.session = self
        self.stage = 'new'
        self.uploaded = b''
        self.posts = []
    def _get_authenticated_page(self, url):
        status = {'new': 'No submission', 'draft': 'Draft (not submitted)', 'submitted': 'Submitted for grading'}[self.stage]
        filelink = '<a href="/pluginfile.php/1/work.pdf">work.pdf</a>' if self.stage != 'new' else ''
        html = f'''<div id="page-header"><h1>Work</h1></div><div id="region-main">
          <div class="submissionstatustable"><table><tr><th>Submission status</th><td>{status}</td></tr>
          <tr><th>File submissions</th><td>{filelink}</td></tr></table></div>
          <form method="get" action="/mod/assign/view.php"><input name="action" value="editsubmission"></form></div>'''
        return html, url
    def get(self, url, params=None, **kwargs):
        if '/pluginfile.php/' in url:
            return Response(url, content=self.uploaded)
        action = params['action']
        target = f'{self.base_url}/mod/assign/view.php?id=25&action={action}'
        fields = '<input type="hidden" name="id" value="25"><input type="hidden" name="sesskey" value="secret">'
        if action == 'editsubmission':
            html = f'''<form method="post" action="/mod/assign/view.php">{fields}
                <input type="hidden" name="action" value="savesubmission">
                <input type="hidden" name="files_filemanager" value="3"><input type="submit" name="submitbutton" value="Save"></form>
                <script>M.form_filemanager.init(Y, {{"itemid":3,"list":[],"filecount":0,"client_id":"c",
                "maxfiles":2,"maxbytes":2048,"accepted_types":["*"],"context":{{"id":2}},
                "filepicker":{{"repositories":{{"5":{{"type":"upload"}}}}}}}});</script>'''
        else:
            html = f'''<form method="post" action="/mod/assign/view.php">{fields}
                <input type="hidden" name="action" value="confirmsubmit">
                <label><input type="checkbox" name="submissionstatement" value="1">I agree</label>
                <input type="submit" name="submitbutton" value="Continue"></form>'''
        return Response(target, html)
    def post(self, url, **kwargs):
        self.posts.append(url)
        if 'repository_ajax.php' in url:
            self.uploaded = kwargs['files']['repo_upload_file'][1].read()
            return Response(url, data={'id': 3, 'file': 'work.pdf'})
        self.stage = 'submitted' if kwargs['data']['action'] == 'confirmsubmit' else 'draft'
        return Response(url, status=303)


def test_file_save_and_final_submit_verify_server_receipts(tmp_path):
    from tue_api_wrapper.moodle_submission_write import review_file, save_file
    from tue_api_wrapper.moodle_submission_final import review_final, submit_final
    client = FakeMoodle()
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    preview = review_file(client, 25, str(path))
    with pytest.raises(ValueError):
        save_file(client, 25, str(path), preview['file']['sha256'], preview['review_sha256'], confirm=False)
    with pytest.raises(ValueError):
        save_file(client, 25, str(path), preview['file']['sha256'], 'stale review', confirm=True)
    assert client.posts == []
    saved = save_file(client, 25, str(path), preview['file']['sha256'], preview['review_sha256'], confirm=True)
    assert saved['outcome'] == 'draft' and saved['file_verified']
    final = review_final(client, 25, str(path))
    with pytest.raises(ValueError):
        submit_final(client, 25, str(path), preview['file']['sha256'], final['confirmation_sha256'], confirm=True)
    with pytest.raises(ValueError):
        submit_final(client, 25, str(path), preview['file']['sha256'], 'stale text',
                     confirm=True, accept_statement=True)
    assert len(client.posts) == 2
    result = submit_final(client, 25, str(path), preview['file']['sha256'], final['confirmation_sha256'],
                          confirm=True, accept_statement=True)
    assert result['outcome'] == 'submitted' and result['file_verified']


def test_form_refuses_external_post_target():
    from tue_api_wrapper.moodle_submission_forms import parse_form
    html = '''<form method="post" action="https://evil.example/mod/assign/view.php">
    <input name="id" value="25"><input name="action" value="savesubmission"></form>'''
    with pytest.raises(AlmaParseError):
        parse_form(html, 'https://moodle.example/mod/assign/view.php?id=25', 25, 'savesubmission')


def test_save_does_not_treat_http_200_as_receipt(tmp_path):
    from tue_api_wrapper.moodle_submission_write import review_file, save_file
    class RejectedSave(FakeMoodle):
        def post(self, url, **kwargs):
            if 'repository_ajax.php' not in url:
                self.posts.append(url)
                return Response(url, '<html>validation error</html>')
            return super().post(url, **kwargs)
    client = RejectedSave()
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    preview = review_file(client, 25, str(path))
    result = save_file(client, 25, str(path), preview['file']['sha256'], preview['review_sha256'], confirm=True)
    assert result['outcome'] == 'unknown'
    assert result['file_verified'] is False


def test_mcp_review_and_save_use_the_shared_flow(monkeypatch, tmp_path):
    from tue_api_wrapper import mcp_moodle_write
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    moodle = FakeMoodle()
    client = SimpleNamespace(moodle=SimpleNamespace(client=moodle), close=lambda: None)
    monkeypatch.setattr(mcp_moodle_write, 'make_client', lambda _: (client, 'student'))
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    mcp_moodle_write.register_moodle_write_tools(Server(), None)
    preview = tools['moodle_submission_review'](25, str(path))
    result = tools['moodle_submission_save'](25, str(path), preview['file']['sha256'],
                                             preview['review_sha256'], confirm=True)
    assert result['outcome'] == 'draft'


def test_cli_and_mcp_require_confirmation_before_connecting(monkeypatch, tmp_path):
    from tue_api_wrapper import moodle_submission_cli, mcp_moodle_write
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    def forbidden(*args):
        raise AssertionError('must not connect')
    monkeypatch.setattr(moodle_submission_cli, 'make_client', forbidden)
    monkeypatch.setattr(mcp_moodle_write, 'make_client', forbidden)
    with pytest.raises(SystemExit):
        moodle_submission_cli.main(['save', '--assignment-id', '25', '--file', str(path), '--sha256', 'a'])
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    mcp_moodle_write.register_moodle_write_tools(Server(), None)
    with pytest.raises(ValueError):
        tools['moodle_submission_save'](25, str(path), 'a', 'b')
    with pytest.raises(ValueError):
        tools['moodle_submission_submit'](25, str(path), 'a', 'b')


def test_moodle_writes_are_opt_in():
    from tue_api_wrapper.mcp_server import _enabled_services
    assert 'moodle-write' not in _enabled_services(None)
    assert 'moodle-write' in _enabled_services(['moodle-write'])

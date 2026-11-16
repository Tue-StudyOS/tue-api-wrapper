import json

import pytest

from test_moodle_submission_actions import FakeMoodle, Response
from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_submission_write import review_file, save_file


class RotatingComments(FakeMoodle):
    serial = 0

    def _get_authenticated_page(self, url):
        html, url = super()._get_authenticated_page(url)
        self.serial += 1
        row = ('<tr><th>Submission comments</th><td>Comments (0)'
               f'<a href="?id=25&useridlistid={self.serial}&nonjscomment=1">Show comments</a></td></tr>')
        return html.replace('</table>', row + '</table>'), url


def test_rotating_comment_links_do_not_reject_unchanged_submission(tmp_path):
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    client = RotatingComments()
    first = review_file(client, 25, str(path))
    second = review_file(client, 25, str(path))
    assert first['review_sha256'] == second['review_sha256']
    result = save_file(client, 25, str(path), first['file']['sha256'], first['review_sha256'], confirm=True)
    assert result['file_verified']


def test_real_status_change_still_rejects_review(tmp_path):
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'coursework')
    client = RotatingComments()
    preview = review_file(client, 25, str(path))
    client.stage = 'submitted'
    with pytest.raises(ValueError, match='state changed'):
        save_file(client, 25, str(path), preview['file']['sha256'], preview['review_sha256'], confirm=True)
    assert client.posts == []


class ExistingSubmission(FakeMoodle):
    def __init__(self):
        super().__init__()
        self.stage = 'submitted'
        self.saved = {'work.pdf': b'old report', 'source.zip': b'unchanged source'}
        self.draft = dict(self.saved)

    def _get_authenticated_page(self, url):
        html, url = super()._get_authenticated_page(url)
        links = ''.join(f'<a href="/pluginfile.php/1/{name}">{name}</a>' for name in self.saved)
        html = html.replace('<a href="/pluginfile.php/1/work.pdf">work.pdf</a>', links)
        return html, url

    def get(self, url, params=None, **kwargs):
        if '/pluginfile.php/' in url:
            return Response(url, content=self.saved[url.rsplit('/', 1)[-1]])
        if '/draftfile.php/' in url:
            return Response(url, content=self.draft[url.rsplit('/', 1)[-1]])
        response = super().get(url, params=params, **kwargs)
        listing = [{'filename': name, 'filepath': '/', 'filesize': len(data),
                    'url': f'{self.base_url}/draftfile.php/1/{name}'} for name, data in self.draft.items()]
        response.text = response.text.replace('"list":[],"filecount":0',
                                              f'"list":{json.dumps(listing)},"filecount":{len(listing)}')
        return response

    def post(self, url, **kwargs):
        self.posts.append(url)
        if 'draftfiles_ajax.php' in url:
            data = kwargs['data']
            assert data['action'] == 'delete' and data['filename'] == 'work.pdf'
            assert data['filepath'] == '/' and str(data['itemid']) == '3'
            self.draft.pop(data['filename'])
            return Response(url, data={'filepath': '/'})
        if 'repository_ajax.php' in url:
            name, stream = kwargs['files']['repo_upload_file']
            self.draft[name] = stream.read()
            return Response(url, data={'id': 3, 'file': name})
        self.saved = dict(self.draft)
        return Response(url, status=303)


def test_replacement_requires_opt_in_and_preserves_other_file(tmp_path):
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'updated report')
    client = ExistingSubmission()
    with pytest.raises(AlmaParseError):
        review_file(client, 25, str(path))
    preview = review_file(client, 25, str(path), replace_existing=True)
    result = save_file(client, 25, str(path), preview['file']['sha256'],
                       preview['review_sha256'], confirm=True, replace_existing=True)
    assert result['outcome'] == 'submitted'
    assert result['file_verified'] and result['preserved_files_verified']
    assert client.saved == {'work.pdf': b'updated report', 'source.zip': b'unchanged source'}


def test_replacement_rejects_changed_original_without_writing(tmp_path):
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'updated report')
    client = ExistingSubmission()
    preview = review_file(client, 25, str(path), replace_existing=True)
    client.saved['work.pdf'] = b'changed by partner'
    client.draft['work.pdf'] = client.saved['work.pdf']
    with pytest.raises(ValueError, match='state changed'):
        save_file(client, 25, str(path), preview['file']['sha256'],
                  preview['review_sha256'], confirm=True, replace_existing=True)
    assert client.posts == []


def test_unreviewed_draft_changes_block_replacement(tmp_path):
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'updated report')
    client = ExistingSubmission()
    client.draft['source.zip'] = b'unreviewed browser draft'
    with pytest.raises(AlmaParseError, match='draft files differ'):
        review_file(client, 25, str(path), replace_existing=True)
    assert client.posts == []


def test_failed_upload_does_not_save_deleted_draft_target(tmp_path):
    class FailedUpload(ExistingSubmission):
        def post(self, url, **kwargs):
            if 'repository_ajax.php' in url:
                raise RuntimeError('network failure')
            return super().post(url, **kwargs)
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'updated report')
    client = FailedUpload()
    preview = review_file(client, 25, str(path), replace_existing=True)
    with pytest.raises(AlmaParseError, match='outcome is unknown'):
        save_file(client, 25, str(path), preview['file']['sha256'],
                  preview['review_sha256'], confirm=True, replace_existing=True)
    assert client.saved == {'work.pdf': b'old report', 'source.zip': b'unchanged source'}
    assert len(client.posts) == 1


def test_cli_reviews_and_replaces_through_shared_library(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace
    from tue_api_wrapper import moodle_submission_cli
    path = tmp_path / 'work.pdf'
    path.write_bytes(b'updated report')
    moodle = ExistingSubmission()
    client = SimpleNamespace(moodle=SimpleNamespace(client=moodle), close=lambda: None)
    monkeypatch.setattr(moodle_submission_cli, 'make_client', lambda _: (client, 'student'))
    args = ['--assignment-id', '25', '--file', str(path), '--replace-existing']
    assert moodle_submission_cli.main(['review', *args]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview['replace_existing'] is True
    assert moodle_submission_cli.main(['save', *args, '--confirm', '--sha256', preview['file']['sha256'],
                                       '--review-sha256', preview['review_sha256']]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['file_verified'] and result['preserved_files_verified']
    assert moodle.saved['work.pdf'] == b'updated report'


def test_replacement_missing_target_does_not_become_an_add(tmp_path):
    path = tmp_path / 'absent.pdf'
    path.write_bytes(b'report')
    client = ExistingSubmission()
    with pytest.raises(AlmaParseError, match='replace'):
        review_file(client, 25, str(path), replace_existing=True)
    assert client.posts == []

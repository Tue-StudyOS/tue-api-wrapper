"""Explicit Moodle file submission writes; no session state is persisted."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from .config import AlmaParseError
from .moodle_assignment import fetch_assignment
from .moodle_submission_actions import classify_receipt, validate_upload_response
from .moodle_submission_forms import file_manager, get_form, parse_form
from .portal_common import serialize


def file_details(path: str) -> dict:
    file = Path(path)
    if not file.is_file():
        raise ValueError('Submission file must be an existing regular file')
    digest = hashlib.sha256()
    with file.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'name': file.name, 'size': file.stat().st_size, 'sha256': digest.hexdigest()}


def _check_file_manager(config: dict, file: dict) -> None:
    limit = int(config.get('maxfiles', -1))
    existing = config.get('list', [])
    if limit >= 0 and int(config.get('filecount', 0)) + 1 > limit:
        raise AlmaParseError('The Moodle file limit would be exceeded')
    if any(f.get('filename') == file['name'] or f.get('name') == file['name'] for f in existing):
        raise AlmaParseError('A draft file with this name already exists; no file was overwritten')
    maxbytes = int(config.get('maxbytes', -1))
    if maxbytes > 0 and file['size'] > maxbytes:
        raise AlmaParseError('The Moodle file size limit would be exceeded')


def review_file(client, assignment_id: int, path: str) -> dict:
    assignment = fetch_assignment(client, assignment_id)
    if 'editsubmission' not in assignment.available_actions:
        raise AlmaParseError('Moodle does not offer an edit-submission action')
    html, url = get_form(client, assignment_id, 'editsubmission')
    soup, form, fields = parse_form(html, url, assignment_id, 'savesubmission')
    if form.select('input[type="checkbox"]'):
        raise AlmaParseError('The submission form requires an additional acknowledgement')
    config = file_manager(soup, fields)
    repos = config.get('filepicker', {}).get('repositories', {})
    if not any(r.get('type') == 'upload' for r in repos.values()):
        raise AlmaParseError('Moodle does not offer a file upload repository')
    file = file_details(path)
    _check_file_manager(config, file)
    limit, maxbytes = int(config.get('maxfiles', -1)), int(config.get('maxbytes', -1))
    stable = [serialize(field) for field in assignment.submission
              if field.label.strip().casefold() not in {'verbleibende zeit', 'time remaining'}]
    fingerprint = hashlib.sha256(json.dumps({'id': assignment_id, 'title': assignment.title,
                                            'instructions': assignment.instructions, 'submission': stable,
                                            'file': file}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {'assignment': serialize(assignment), 'file': file, 'review_sha256': fingerprint,
            'file_limits': {'max_files': limit, 'max_bytes': maxbytes,
                            'accepted_types': config.get('accepted_types')},
            'warning': 'Saving can submit for grading and can affect group members.'}


def save_file(client, assignment_id: int, path: str, expected_sha256: str, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review = review_file(client, assignment_id, path)
    if review['file']['sha256'] != expected_sha256:
        raise ValueError('File hash changed or does not match the reviewed file')
    if review['review_sha256'] != review_sha256:
        raise ValueError('Moodle assignment state changed since review')
    html, url = get_form(client, assignment_id, 'editsubmission')
    soup, form, fields = parse_form(html, url, assignment_id, 'savesubmission')
    if form.select('input[type="checkbox"]'):
        raise AlmaParseError('The submission form requires an additional acknowledgement')
    config = file_manager(soup, fields)
    _check_file_manager(config, review['file'])
    repos = config.get('filepicker', {}).get('repositories', {})
    upload = [key for key, value in repos.items() if value.get('type') == 'upload']
    if len(upload) != 1:
        raise AlmaParseError('Moodle upload repository is unavailable or ambiguous')
    params = {'action': 'upload', 'repo_id': upload[0], 'env': 'filemanager',
              'sesskey': fields['sesskey'], 'client_id': config.get('client_id'),
              'itemid': fields['files_filemanager'], 'maxbytes': config.get('maxbytes', -1),
              'areamaxbytes': config.get('areamaxbytes', -1), 'savepath': '/',
              'ctx_id': config.get('context', {}).get('id'),
              'accepted_types[]': config.get('accepted_types', ['*'])}
    params = {k: v for k, v in params.items() if v is not None}
    # Hash the same open file immediately before sending it.
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != expected_sha256:
            raise ValueError('File changed after review')
        stream.seek(0)
        try:
            response = client.session.post(f'{client.base_url}/repository/repository_ajax.php?action=upload',
                                           data={k: v for k, v in params.items() if k != 'action'},
                                           files={'repo_upload_file': (review['file']['name'], stream)},
                                           timeout=client.timeout_seconds, allow_redirects=False)
            response.raise_for_status()
            if response.status_code != 200:
                raise AlmaParseError('Upload response was not successful')
            validate_upload_response(response.json(), review['file']['name'], fields['files_filemanager'])
            response = client.session.post(f'{client.base_url}/mod/assign/view.php', data=fields,
                                           timeout=client.timeout_seconds, allow_redirects=False)
            response.raise_for_status()
            if response.status_code not in {200, 302, 303}:
                raise AlmaParseError('Save response was not recognized')
            return verify_file_receipt(client, assignment_id, review['file'])
        except Exception:
            raise AlmaParseError('Upload or save outcome is unknown; inspect Moodle before retrying') from None


def verify_file_receipt(client, assignment_id: int, file: dict) -> dict:
    assignment = fetch_assignment(client, assignment_id)
    matches = [link for field in assignment.submission for link in field.links if link.label == file['name']]
    verified = False
    if len(matches) == 1:
        url = urlparse(matches[0].url)
        if (url.scheme == urlparse(client.base_url).scheme and url.netloc == urlparse(client.base_url).netloc
                and url.path.startswith('/pluginfile.php/')):
            response = client.session.get(matches[0].url, timeout=client.timeout_seconds,
                                          allow_redirects=False, stream=True)
            if response.status_code == 200:
                digest, size = hashlib.sha256(), 0
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > file['size']:
                        break
                    digest.update(chunk)
                verified = size == file['size'] and digest.hexdigest() == file['sha256']
            response.close()
    return {'assignment_id': assignment_id, 'file': file, 'file_verified': verified,
            'outcome': classify_receipt(assignment.submission, verified),
            'submission': serialize(assignment.submission)}

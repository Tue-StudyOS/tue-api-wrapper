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
from .moodle_submission_state import check_draft_files, remove_draft_target, stable_submission, submitted_files


def file_details(path: str) -> dict:
    file = Path(path)
    if not file.is_file():
        raise ValueError('Submission file must be an existing regular file')
    digest = hashlib.sha256()
    with file.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'name': file.name, 'size': file.stat().st_size, 'sha256': digest.hexdigest()}


def _check_file_manager(config: dict, file: dict, *, replace_existing: bool = False) -> None:
    limit = int(config.get('maxfiles', -1))
    existing = config.get('list', [])
    matches = [f for f in existing if f.get('filename') == file['name'] or f.get('name') == file['name']]
    if replace_existing and (len(matches) != 1 or matches[0].get('filepath') != '/'):
        raise AlmaParseError('Cannot replace: exactly one root-level file with this name is required')
    if limit >= 0 and int(config.get('filecount', 0)) + (0 if replace_existing else 1) > limit:
        raise AlmaParseError('The Moodle file limit would be exceeded')
    if matches and not replace_existing:
        raise AlmaParseError('A draft file with this name already exists; no file was overwritten')
    maxbytes = int(config.get('maxbytes', -1))
    if maxbytes > 0 and file['size'] > maxbytes:
        raise AlmaParseError('The Moodle file size limit would be exceeded')


def review_file(client, assignment_id: int, path: str, *, replace_existing: bool = False) -> dict:
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
    _check_file_manager(config, file, replace_existing=replace_existing)
    originals = submitted_files(client, assignment) if replace_existing else []
    if replace_existing:
        if not any(original['name'] == file['name'] for original in originals):
            raise AlmaParseError('Cannot replace a file that is not in the saved submission')
        check_draft_files(client, config, originals)
    limit, maxbytes = int(config.get('maxfiles', -1)), int(config.get('maxbytes', -1))
    stable = stable_submission(assignment.submission)
    fingerprint = hashlib.sha256(json.dumps({'id': assignment_id, 'title': assignment.title,
                                            'instructions': assignment.instructions, 'submission': stable,
                                            'file': file, 'replace_existing': replace_existing,
                                            'original_files': originals,
                                            'limits': [limit, maxbytes, config.get('accepted_types')]},
                                           sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {'assignment': serialize(assignment), 'file': file, 'review_sha256': fingerprint,
            'file_limits': {'max_files': limit, 'max_bytes': maxbytes,
                            'accepted_types': config.get('accepted_types')},
            'replace_existing': replace_existing, 'original_files': originals,
            'warning': 'Saving can submit for grading and can affect group members.'}


def save_file(client, assignment_id: int, path: str, expected_sha256: str, review_sha256: str, *,
              confirm: bool, replace_existing: bool = False) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review = review_file(client, assignment_id, path, replace_existing=replace_existing)
    if review['file']['sha256'] != expected_sha256:
        raise ValueError('File hash changed or does not match the reviewed file')
    if review['review_sha256'] != review_sha256:
        raise ValueError('Moodle assignment state changed since review')
    html, url = get_form(client, assignment_id, 'editsubmission')
    soup, form, fields = parse_form(html, url, assignment_id, 'savesubmission')
    if form.select('input[type="checkbox"]'):
        raise AlmaParseError('The submission form requires an additional acknowledgement')
    config = file_manager(soup, fields)
    _check_file_manager(config, review['file'], replace_existing=replace_existing)
    if replace_existing:
        check_draft_files(client, config, review['original_files'])
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
            if replace_existing:
                remove_draft_target(client, fields, review['file']['name'])
            response = client.session.post(f'{client.base_url}/repository/repository_ajax.php?action=upload',
                                           data={k: v for k, v in params.items() if k != 'action'},
                                           files={'repo_upload_file': (review['file']['name'], stream)},
                                           timeout=client.timeout_seconds, allow_redirects=False)
            response.raise_for_status()
            if response.status_code != 200:
                raise AlmaParseError('Upload response was not successful')
            validate_upload_response(response.json(), review['file']['name'], fields['files_filemanager'])
            if replace_existing and submitted_files(client, fetch_assignment(client, assignment_id)) != review['original_files']:
                raise AlmaParseError('Saved files changed during replacement; draft was not saved')
            response = client.session.post(f'{client.base_url}/mod/assign/view.php', data=fields,
                                           timeout=client.timeout_seconds, allow_redirects=False)
            response.raise_for_status()
            if response.status_code not in {200, 302, 303}:
                raise AlmaParseError('Save response was not recognized')
            receipt = verify_file_receipt(client, assignment_id, review['file'])
            if replace_existing:
                current = submitted_files(client, fetch_assignment(client, assignment_id))
                expected = sorted([f for f in review['original_files'] if f['name'] != review['file']['name']]
                                  + [review['file']], key=lambda file: file['name'])
                receipt['preserved_files_verified'] = current == expected
                if not receipt['preserved_files_verified']:
                    receipt['outcome'] = 'unknown'
            return receipt
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

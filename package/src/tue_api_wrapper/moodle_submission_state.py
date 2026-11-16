"""Stable review state and byte checks for Moodle file replacements."""
from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .config import AlmaParseError
from .portal_common import serialize


def stable_submission(fields) -> list[dict]:
    result = []
    for field in fields:
        label = field.label.strip().casefold()
        if label in {'verbleibende zeit', 'time remaining'}:
            continue
        value = serialize(field)
        if label in {'abgabekommentare', 'submission comments'}:
            for link in value['links']:
                url = urlparse(link['url'])
                query = [(k, v) for k, v in parse_qsl(url.query, keep_blank_values=True) if k != 'useridlistid']
                link['url'] = urlunparse(url._replace(query=urlencode(query)))
        result.append(value)
    return result


def remote_file(client, name: str, url: str, *, draft: bool = False) -> dict:
    target, origin = urlparse(url), urlparse(client.base_url)
    prefix = '/draftfile.php/' if draft else '/pluginfile.php/'
    if (target.scheme, target.netloc) != (origin.scheme, origin.netloc) or not target.path.startswith(prefix):
        raise AlmaParseError('Moodle file URL is outside the expected file area')
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False, stream=True)
    try:
        response.raise_for_status()
        if response.status_code != 200:
            raise AlmaParseError('Moodle file could not be read for replacement review')
        digest, size = hashlib.sha256(), 0
        for chunk in response.iter_content(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
        return {'name': name, 'size': size, 'sha256': digest.hexdigest()}
    finally:
        response.close()


def submitted_files(client, assignment) -> list[dict]:
    files = []
    for field in assignment.submission:
        if field.label.strip().casefold() not in {'dateiabgabe', 'file submissions'}:
            continue
        files.extend(remote_file(client, link.label, link.url) for link in field.links)
    names = [file['name'] for file in files]
    if len(names) != len(set(names)):
        raise AlmaParseError('Moodle submission contains ambiguous filenames')
    return sorted(files, key=lambda file: file['name'])


def check_draft_files(client, config: dict, expected: list[dict]) -> None:
    actual = []
    for entry in config.get('list', []):
        if entry.get('filepath') != '/' or not entry.get('filename') or not entry.get('url'):
            raise AlmaParseError('Replacement requires a complete root-level draft file listing')
        actual.append(remote_file(client, entry['filename'], entry['url'], draft=True))
    if sorted(actual, key=lambda file: file['name']) != expected:
        raise AlmaParseError('Moodle draft files differ from the submitted files; inspect before replacing')


def remove_draft_target(client, fields: dict, name: str) -> None:
    response = client.session.post(f'{client.base_url}/repository/draftfiles_ajax.php',
                                   data={'action': 'delete', 'sesskey': fields['sesskey'],
                                         'itemid': fields['files_filemanager'], 'filepath': '/', 'filename': name},
                                   timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200 or response.json() != {'filepath': '/'}:
        raise AlmaParseError('Moodle did not confirm removal of the replacement target from the draft')

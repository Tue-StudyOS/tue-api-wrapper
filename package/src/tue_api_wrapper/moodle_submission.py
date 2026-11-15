"""Inspect the Moodle submission form without sending a submission."""
from __future__ import annotations

import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_assignment import fetch_assignment


def inspect_submission(client, assignment_id: int) -> dict:
    assignment = fetch_assignment(client, assignment_id)
    if 'editsubmission' not in assignment.available_actions:
        raise AlmaParseError('Moodle does not currently offer an edit-submission action')
    response = client.session.get(f'{client.base_url}/mod/assign/view.php',
                                  params={'id': assignment_id, 'action': 'editsubmission'},
                                  timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    parsed = urlparse(response.url)
    if (parsed.netloc != urlparse(client.base_url).netloc or parsed.path != '/mod/assign/view.php'
            or parse_qs(parsed.query).get('id') != [str(assignment_id)]
            or parse_qs(parsed.query).get('action') != ['editsubmission']):
        raise AlmaParseError('Moodle did not return the requested submission form')
    result = inspect_submission_form(response.text, response.url, assignment_id)
    result['assignment'] = assignment
    return result


def inspect_submission_form(html: str, page_url: str, assignment_id: int) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    matching = []
    for form in soup.select('form[method]'):
        target = urlparse(urljoin(page_url, form.get('action', '')))
        action = form.select_one('input[name="action"]')
        ident = form.select_one('input[name="id"]')
        if (form['method'].lower() == 'post' and target.netloc == urlparse(page_url).netloc
                and target.path == '/mod/assign/view.php' and action and action.get('value') == 'savesubmission'
                and ident and ident.get('value') == str(assignment_id)):
            matching.append(form)
    if len(matching) != 1:
        raise AlmaParseError('Moodle did not return a recognizable submission form')
    form = matching[0]
    manager = None
    marker = 'M.form_filemanager.init(Y, '
    if form.select_one('input[name="files_filemanager"]'):
        configs = []
        for script in soup.select('script'):
            text = script.string or script.get_text()
            if marker in text:
                try:
                    value, _ = json.JSONDecoder().raw_decode(text.split(marker, 1)[1].lstrip())
                    configs.append(value)
                except (ValueError, TypeError) as error:
                    raise AlmaParseError('Moodle file manager configuration could not be parsed') from error
        item = form.select_one('input[name="files_filemanager"]').get('value')
        configs = [c for c in configs if str(c.get('itemid')) == item]
        if len(configs) != 1:
            raise AlmaParseError('Moodle file manager configuration did not match the form')
        config = configs[0]
        repositories = config.get('filepicker', {}).get('repositories', {})
        manager = {'max_files': config.get('maxfiles'), 'max_bytes': config.get('maxbytes'),
                   'current_files': config.get('filecount'), 'accepted_types': config.get('accepted_types'),
                   'upload_available': any(repo.get('type') == 'upload' for repo in repositories.values())}
    return {'assignment_id': assignment_id, 'form_available': True, 'file_manager': manager,
            'input_names': sorted({n.get('name') for n in form.select('input[name], textarea[name], select[name]')
                                   if n.get('name') not in {'sesskey', 'userid', 'lastmodified'}}),
            'submission_performed': False}

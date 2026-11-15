"""Extract supported Moodle submission forms, keeping transient fields private."""
from __future__ import annotations

import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


def get_form(client, assignment_id: int, action: str):
    if action not in {'editsubmission', 'submit'}:
        raise ValueError('Unsupported Moodle assignment form')
    response = client.session.get(f'{client.base_url}/mod/assign/view.php',
                                  params={'id': assignment_id, 'action': action},
                                  timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    u = urlparse(response.url)
    if (response.status_code != 200 or u.netloc != urlparse(client.base_url).netloc
            or u.path != '/mod/assign/view.php' or parse_qs(u.query).get('id') != [str(assignment_id)]
            or parse_qs(u.query).get('action') != [action]):
        raise AlmaParseError('Moodle did not return the requested submission form')
    return response.text, response.url


def parse_form(html: str, page_url: str, assignment_id: int, action: str):
    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    for form in soup.select('form[method]'):
        target = urlparse(urljoin(page_url, form.get('action', '')))
        hidden_action = form.select_one('input[name="action"]')
        ident = form.select_one('input[name="id"]')
        if (form['method'].lower() == 'post' and target.netloc == urlparse(page_url).netloc
                and target.scheme == urlparse(page_url).scheme and target.path == '/mod/assign/view.php' and not target.query
                and hidden_action and hidden_action.get('value') == action
                and ident and ident.get('value') == str(assignment_id)):
            matches.append(form)
    if len(matches) != 1:
        raise AlmaParseError('Moodle did not return a supported submission form')
    form = matches[0]
    if form.select('textarea, select, input:not([type="hidden"]):not([type="submit"]):not([type="checkbox"])'):
        raise AlmaParseError('Moodle requires additional input; use the browser for this submission')
    fields = {}
    for node in form.select('input[type="hidden"][name]'):
        name = node['name']
        if name in fields:
            raise AlmaParseError('Moodle form contains duplicate fields')
        fields[name] = node.get('value', '')
    if not fields.get('sesskey'):
        raise AlmaParseError('Moodle form did not include a session key')
    button = form.select_one('input[type="submit"][name="submitbutton"]')
    if button:
        fields['submitbutton'] = button.get('value', '')
    return soup, form, fields


def file_manager(soup, fields: dict) -> dict:
    item = fields.get('files_filemanager')
    marker = 'M.form_filemanager.init(Y, '
    configs = []
    for script in soup.select('script'):
        text = script.string or script.get_text()
        for part in text.split(marker)[1:]:
            try:
                value, _ = json.JSONDecoder().raw_decode(part.lstrip())
                if str(value.get('itemid')) == item:
                    configs.append(value)
            except (ValueError, AttributeError):
                raise AlmaParseError('Moodle file manager configuration could not be parsed')
    if not item or len(configs) != 1:
        raise AlmaParseError('Moodle file manager does not match the submission form')
    return configs[0]

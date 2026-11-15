"""Read the currently visible questions in an existing Moodle quiz attempt."""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


def parse_attempt(html: str, page_url: str, attempt_id: int) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.select_one('form#responseform')
    if not form or not form.select_one(f'input[name="attempt"][value="{attempt_id}"]'):
        raise AlmaParseError('Moodle did not return the requested in-progress attempt')
    questions = []
    for question in form.select('.que'):
        text = question.select_one('.qtext')
        if not text:
            raise AlmaParseError('Moodle returned a question without recognizable text')
        grouped = {}
        for control in question.select('input[name], textarea[name], select[name]'):
            kind = control.get('type', 'text').lower() if control.name == 'input' else control.name
            if kind in {'hidden', 'submit', 'button'} or control.has_attr('disabled'):
                continue
            if kind not in {'radio', 'checkbox', 'text', 'textarea', 'select'}:
                raise AlmaParseError('Moodle question uses an unsupported input type')
            name = control['name']
            if name in grouped and kind in {'text', 'textarea', 'select'}:
                raise AlmaParseError('Moodle question contains duplicate input fields')
            entry = grouped.setdefault(name, {'name': name, 'type': kind, 'value': None, 'options': []})
            if entry['type'] != kind:
                raise AlmaParseError('Moodle question contains ambiguous input fields')
            if kind in {'radio', 'checkbox'}:
                label = question.find('label', attrs={'for': control.get('id')}) if control.get('id') else None
                entry['options'].append({'value': control.get('value', 'on'),
                                         'label': label.get_text(' ', strip=True) if label else None,
                                         'selected': control.has_attr('checked')})
            elif kind == 'select':
                entry['options'] = [{'value': o.get('value', o.get_text()), 'label': o.get_text(' ', strip=True),
                                     'selected': o.has_attr('selected')} for o in control.select('option')]
                if entry['options'] and not control.has_attr('multiple') and not any(o['selected'] for o in entry['options']):
                    entry['options'][0]['selected'] = True
            else:
                entry['value'] = control.get('value', '') if kind == 'text' else control.get_text()
        questions.append({'id': question.get('id'), 'type': [c for c in question.get('class', []) if c != 'que'],
                          'text': text.get_text(' ', strip=True), 'fields': list(grouped.values())})
    if not questions:
        raise AlmaParseError('Moodle attempt has no recognizable questions on this page')
    current = form.select_one('input[name="thispage"]')
    return {'attempt_id': attempt_id, 'source_url': page_url,
            'page': int(current.get('value', '0')) if current and current.get('value', '0').isdigit() else None,
            'questions': questions, 'coverage': 'visible_attempt_page'}


def fetch_attempt(client, attempt_id: int, *, page: int = 0) -> dict:
    if (isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1
            or isinstance(page, bool) or not isinstance(page, int) or page < 0):
        raise ValueError('Attempt ID must be positive and page nonnegative')
    url = f'{client.base_url}/mod/quiz/attempt.php?attempt={attempt_id}&page={page}'
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    parsed = urlparse(response.url)
    if (response.status_code != 200 or parsed.netloc != urlparse(client.base_url).netloc
            or parsed.path != '/mod/quiz/attempt.php' or parse_qs(parsed.query).get('attempt') != [str(attempt_id)]):
        raise AlmaParseError('Moodle did not return the requested in-progress attempt')
    return parse_attempt(response.text, response.url, attempt_id)

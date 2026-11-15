"""Review and save supported answers to an existing Moodle attempt page."""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_quiz_attempt import fetch_attempt, parse_attempt


def prepare_answer_form(html: str, page_url: str, attempt_id: int, answers: dict[str, list[str]]):
    public = parse_attempt(html, page_url, attempt_id)
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.select_one('form#responseform')
    action = urlparse(urljoin(page_url, form.get('action', '')))
    if (form.get('method', '').lower() != 'post' or action.netloc != urlparse(page_url).netloc
            or action.scheme != urlparse(page_url).scheme or action.path != '/mod/quiz/processattempt.php'
            or set(parse_qs(action.query)) - {'cmid'}):
        raise AlmaParseError('Moodle attempt form has an unsupported action')
    hidden = [(n['name'], n.get('value', '')) for n in form.select('input[type="hidden"][name]')]
    pairs = dict(hidden)
    if (len(pairs) != len(hidden) or pairs.get('attempt') != str(attempt_id) or not pairs.get('sesskey')
            or pairs.get('finishattempt', '0') != '0' or pairs.get('timeup', '0') != '0'):
        raise AlmaParseError('Moodle attempt form is missing fields or is ready to finish')
    all_fields = [f for q in public['questions'] for f in q['fields']]
    fields = {f['name']: f for f in all_fields}
    if len(fields) != len(all_fields) or any(not re.match(r'^q[0-9]+:[0-9]+_', name) for name in fields):
        raise AlmaParseError('Moodle returned unsupported or duplicate answer fields')
    if not isinstance(answers, dict) or set(answers) - fields.keys():
        raise ValueError('Answers must refer only to visible question fields')
    if not answers:
        raise ValueError('At least one answer is required')
    for name, values in answers.items():
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ValueError('Each answer must be a list of strings')
        field = fields[name]
        allowed = {o['value'] for o in field['options']}
        if field['type'] in {'radio', 'checkbox', 'select'} and not set(values) <= allowed:
            raise ValueError('An answer is not one of the displayed options')
        if field['type'] in {'radio', 'text', 'textarea', 'select'} and len(values) > 1:
            raise ValueError('This question field accepts at most one value')
    payload = list(hidden)
    for name, field in fields.items():
        if name in answers:
            values = answers[name]
        elif field['type'] in {'radio', 'checkbox', 'select'}:
            values = [o['value'] for o in field['options'] if o['selected']]
        else:
            values = [field['value'] or '']
        payload.extend((name, value) for value in values)
    stable_hidden = [(k, v) for k, v in hidden if k != 'sesskey']
    review = {'attempt': public, 'answers': answers}
    review['review_sha256'] = hashlib.sha256(json.dumps({'review': review, 'state': stable_hidden},
                                         sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review, payload, action.geturl()


def _prepare(client, attempt_id: int, page: int, answers: dict):
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
    review, payload, action = prepare_answer_form(response.text, response.url, attempt_id, answers)
    if review['attempt']['page'] != page:
        raise AlmaParseError('Moodle returned a different attempt page')
    return review, payload, action


def review_answers(client, attempt_id: int, page: int, answers: dict) -> dict:
    review, _, _ = _prepare(client, attempt_id, page, answers)
    return review


def save_answers(client, attempt_id: int, page: int, answers: dict, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review, payload, action = _prepare(client, attempt_id, page, answers)
    if review['review_sha256'] != review_sha256:
        raise ValueError('Quiz questions or attempt state changed since review')
    try:
        response = client.session.post(action, data=payload, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code not in {200, 302, 303}:
            raise AlmaParseError('Unexpected save response')
        observed = fetch_attempt(client, attempt_id, page=page)
        fields = {f['name']: f for q in observed['questions'] for f in q['fields']}
        for name, expected in answers.items():
            field = fields.get(name)
            if not field:
                return {'outcome': 'unknown', 'attempt_id': attempt_id, 'page': page}
            actual = ([o['value'] for o in field['options'] if o['selected']]
                      if field['type'] in {'radio', 'checkbox', 'select'} else [field['value'] or ''])
            if sorted(actual) != sorted(expected):
                return {'outcome': 'unknown', 'attempt_id': attempt_id, 'page': page}
        return {'outcome': 'saved', 'attempt_id': attempt_id, 'page': page}
    except Exception:
        raise AlmaParseError('Answer save outcome is unknown; inspect Moodle before retrying') from None

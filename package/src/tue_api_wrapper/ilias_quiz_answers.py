"""Review and save supported ILIAS question answers."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qs, urlparse

from .config import AlmaParseError
from .ilias_quiz_attempt import open_question, parse_question, question_form


def prepare_answers(html: str, page_url: str, quiz_id: int, answers: dict[str, list[str]]):
    public, form, action = question_form(html, page_url, quiz_id)
    fields = {f['name']: f for f in public['question']['fields']}
    if not isinstance(answers, dict) or not answers or set(answers) - fields.keys():
        raise ValueError('Provide at least one answer using visible field names')
    for name, values in answers.items():
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ValueError('Each answer must be a list of strings')
        field = fields[name]
        if field['type'] in {'radio', 'checkbox'}:
            if not set(values) <= {o['value'] for o in field['options']}:
                raise ValueError('An answer is not a displayed option')
        if len(values) > 1:
            raise ValueError('This field accepts at most one value')
    hidden = {}
    for node in form.select('input[type="hidden"][name]'):
        name, value = node['name'], node.get('value', '')
        if name.startswith('cmd') or (name in hidden and hidden[name] != value):
            raise AlmaParseError('ILIAS question form contains unsupported hidden fields')
        hidden[name] = value
    if not hidden.get('formtimestamp', '').isdigit():
        raise AlmaParseError('ILIAS question form is missing its timestamp')
    payload = list(hidden.items())
    for name, field in fields.items():
        if name in answers:
            values = answers[name]
        elif field['type'] in {'radio', 'checkbox'}:
            values = [o['value'] for o in field['options'] if o['selected']]
        else:
            values = [field['value'] or '']
        payload.extend((name, value) for value in values)
    payload.append(('cmd[submitSolution]', '1'))
    query = parse_qs(urlparse(action).query)
    stable_query = {k: v for k, v in query.items() if k != 'rtoken'}
    state = {k: v for k, v in hidden.items() if k != 'formtimestamp'}
    review = {'attempt': public, 'answers': answers,
              'warning': 'Saving can lock the answer or trigger immediate feedback, depending on test settings.'}
    review['review_sha256'] = hashlib.sha256(json.dumps({'review': review, 'query': stable_query, 'state': state},
                                         sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review, payload, action


def review_answers(client, quiz_id: int, answers: dict[str, list[str]]) -> dict:
    html, url = open_question(client, quiz_id)
    review, _, _ = prepare_answers(html, url, quiz_id, answers)
    return review


def save_answers(client, quiz_id: int, answers: dict[str, list[str]], review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    html, url = open_question(client, quiz_id)
    review, payload, action = prepare_answers(html, url, quiz_id, answers)
    if review['review_sha256'] != review_sha256:
        raise ValueError('ILIAS question or attempt state changed since review')
    try:
        response = client.session.post(action, data=payload, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code not in {200, 302, 303}:
            raise AlmaParseError('Unexpected ILIAS answer response')
        html, url = open_question(client, quiz_id)
        observed = parse_question(html, url, quiz_id)
        if observed['sequence'] != review['attempt']['sequence']:
            return {'outcome': 'unknown', 'quiz_id': quiz_id}
        fields = {f['name']: f for f in observed['question']['fields']}
        for name, expected in answers.items():
            field = fields.get(name)
            if not field:
                return {'outcome': 'unknown', 'quiz_id': quiz_id}
            actual = ([o['value'] for o in field['options'] if o['selected']]
                      if field['type'] in {'radio', 'checkbox'} else [field['value'] or ''])
            if sorted(actual) != sorted(expected):
                return {'outcome': 'unknown', 'quiz_id': quiz_id}
        # ILIAS can redisplay prior POST data after a save error; matching visible
        # values alone do not prove an authorized solution was persisted.
        return {'outcome': 'unverified', 'values_match': True, 'quiz_id': quiz_id,
                'sequence': observed['sequence'], 'message': 'Inspect ILIAS to confirm the answer was saved.'}
    except Exception:
        raise AlmaParseError('ILIAS answer save outcome is unknown; inspect ILIAS before retrying') from None

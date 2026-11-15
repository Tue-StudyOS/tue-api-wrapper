"""Review and explicitly start a Moodle quiz attempt."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_quiz import parse_quiz
from .portal_common import serialize


def parse_start_form(html: str, page_url: str, quiz_id: int) -> dict[str, str]:
    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    for form in soup.select('form[method]'):
        action = urlparse(urljoin(page_url, form.get('action', '')))
        cmid = form.select_one('input[name="cmid"]')
        if (form['method'].lower() == 'post' and action.scheme == urlparse(page_url).scheme
                and action.netloc == urlparse(page_url).netloc and action.path == '/mod/quiz/startattempt.php'
                and not action.query and cmid and cmid.get('value') == str(quiz_id)):
            matches.append(form)
    if len(matches) != 1:
        raise AlmaParseError('Moodle did not expose one supported quiz start form')
    form = matches[0]
    if form.select('textarea, select, input:not([type="hidden"]):not([type="submit"])'):
        raise AlmaParseError('Moodle requires a preflight step; open the quiz in the browser')
    fields = {}
    for node in form.select('input[type="hidden"][name]'):
        if node['name'] in fields:
            raise AlmaParseError('Moodle quiz start form contains duplicate fields')
        fields[node['name']] = node.get('value', '')
    if not fields.get('sesskey') or fields.get('cmid') != str(quiz_id):
        raise AlmaParseError('Moodle quiz start form lacks required session information')
    return fields


def _preview(client, quiz_id: int):
    if isinstance(quiz_id, bool) or not isinstance(quiz_id, int) or quiz_id < 1:
        raise ValueError('Quiz ID must be a positive integer')
    url = f'{client.base_url}/mod/quiz/view.php?id={quiz_id}'
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    parsed = urlparse(response.url)
    if (response.status_code != 200 or parsed.netloc != urlparse(client.base_url).netloc
            or parsed.path != '/mod/quiz/view.php' or parse_qs(parsed.query).get('id') != [str(quiz_id)]):
        raise AlmaParseError('Moodle did not return the requested quiz')
    quiz = parse_quiz(response.text, response.url, quiz_id)
    fields = parse_start_form(response.text, response.url, quiz_id)
    public = {'quiz': serialize(quiz), 'start_fields': {k: v for k, v in fields.items() if k != 'sesskey'}}
    public['review_sha256'] = hashlib.sha256(json.dumps(public, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return public, fields


def review_start(client, quiz_id: int) -> dict:
    public, _ = _preview(client, quiz_id)
    public['warning'] = 'Starting may consume an attempt and start a timer.'
    return public


def start_attempt(client, quiz_id: int, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    public, fields = _preview(client, quiz_id)
    if public['review_sha256'] != review_sha256:
        raise ValueError('Quiz information changed since review')
    try:
        response = client.session.post(f'{client.base_url}/mod/quiz/startattempt.php', data=fields,
                                       timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        target = urlparse(urljoin(client.base_url, response.headers.get('Location', '')))
        attempt = parse_qs(target.query).get('attempt', [])
        if (response.status_code not in {302, 303} or target.netloc != urlparse(client.base_url).netloc
                or target.scheme != urlparse(client.base_url).scheme or target.path != '/mod/quiz/attempt.php'
                or len(attempt) != 1 or not attempt[0].isdigit()):
            return {'outcome': 'unknown', 'message': 'Inspect Moodle before retrying; an attempt may have started.'}
        return {'outcome': 'started', 'quiz_id': quiz_id, 'attempt_id': int(attempt[0])}
    except Exception:
        raise AlmaParseError('Quiz start outcome is unknown; inspect Moodle before retrying') from None

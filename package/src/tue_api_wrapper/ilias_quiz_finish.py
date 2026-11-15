"""Review and explicitly finish an existing ILIAS quiz attempt."""
from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .ilias_quiz_attempt import _player_url, open_question, parse_question
from .ilias_quizzes import fetch_quiz


def finish_link(html: str, page_url: str, quiz_id: int) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    for script in soup.select('script'):
        source = script.string or script.get_text()
        for match in re.findall(r"checkNavigation\(\s*['\"]([^'\"]+)['\"]", source):
            target = urljoin(page_url, html_lib.unescape(match).replace('\\/', '/'))
            try:
                _player_url(target, quiz_id, {'finishTest'})
            except AlmaParseError:
                continue
            candidates.append(target)
    if len(set(candidates)) != 1:
        raise AlmaParseError('ILIAS did not expose one direct finish control; an overview or other step may be required')
    return candidates[0]


def parse_finish_modal(html: str, page_url: str, quiz_id: int):
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    for modal in soup.select('dialog.c-modal--interruptive'):
        form = modal.select_one('form[method]')
        if not form or form['method'].lower() != 'post':
            continue
        action = urljoin(page_url, form.get('action', ''))
        try:
            _player_url(action, quiz_id, {'finishTest'}, allow_final=True)
        except AlmaParseError:
            continue
        if parse_qs(urlparse(action).query).get('finalization_confirmed') != ['confirmed']:
            continue
        message = modal.select_one('.c-modal--interruptive__message')
        title = modal.select_one('.modal-title')
        if not message or not title or form.select('textarea, select, input[type="checkbox"], input[type="radio"]'):
            raise AlmaParseError('ILIAS finish confirmation has unsupported fields')
        if form.select('input[type="hidden"][name]'):
            raise AlmaParseError('ILIAS finish confirmation has unsupported hidden fields')
        candidates.append(({'quiz_id': quiz_id, 'title': title.get_text(' ', strip=True),
                            'message': message.get_text(' ', strip=True)}, action))
    if len(candidates) != 1 or not candidates[0][0]['message']:
        raise AlmaParseError('ILIAS did not return a recognizable finish confirmation')
    return candidates[0]


def _preview(client, quiz_id: int):
    quiz = fetch_quiz(client, f'tst/{quiz_id}')
    question_html, question_url = open_question(client, quiz_id)
    question = parse_question(question_html, question_url, quiz_id)
    url = finish_link(question_html, question_url, quiz_id)
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise AlmaParseError('ILIAS did not return the finish confirmation; inspect the attempt')
    public, action = parse_finish_modal(response.text, response.url, quiz_id)
    public['sequence'] = question['sequence']
    public['completed_attempts_before'] = quiz.completed_attempts
    public['review_sha256'] = hashlib.sha256(json.dumps(public, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return public, action


def review_finish(client, quiz_id: int) -> dict:
    review, _ = _preview(client, quiz_id)
    review['warning'] = 'Finishing submits the attempt and may be irreversible; resuming can restart its timer.'
    return review


def finish_attempt(client, quiz_id: int, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review, action = _preview(client, quiz_id)
    if review['review_sha256'] != review_sha256:
        raise ValueError('ILIAS finish confirmation or attempt state changed since review')
    try:
        response = client.session.post(action, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code not in {200, 302, 303}:
            raise AlmaParseError('Unrecognized finish response')
        after = fetch_quiz(client, f'tst/{quiz_id}').completed_attempts
        before = review['completed_attempts_before']
        confirmed = before is not None and after == before + 1
        return {'outcome': 'finished' if confirmed else 'unknown', 'quiz_id': quiz_id,
                'completed_attempts_before': before, 'completed_attempts_after': after}
    except Exception:
        raise AlmaParseError('ILIAS finish outcome is unknown; inspect ILIAS before retrying') from None

"""Review and explicitly request ILIAS quiz start; response is not a receipt."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .ilias_quizzes import fetch_quiz
from .portal_common import serialize


def parse_start_action(html: str, page_url: str, quiz_id: int) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    actions = []
    for node in soup.select('[data-action]'):
        target = urlparse(urljoin(page_url, node['data-action']))
        query = parse_qs(target.query)
        if (target.scheme == 'https' and target.netloc == 'ovidius.uni-tuebingen.de' and target.path == '/ilias.php'
                and query.get('baseClass') == ['ilrepositorygui'] and query.get('cmd') == ['initTest']
                and query.get('cmdClass') == ['ilTestPlayerFixedQuestionSetGUI'] and query.get('ref_id') == [str(quiz_id)]
                and set(query) <= {'baseClass', 'cmdNode', 'cmdClass', 'cmd', 'ref_id'}):
            actions.append(target.geturl())
    if len(actions) != 1:
        raise AlmaParseError('ILIAS did not expose one supported quiz start action')
    return actions[0]


def _preview(client, quiz_id: int):
    if isinstance(quiz_id, bool) or not isinstance(quiz_id, int) or quiz_id < 1:
        raise ValueError('ILIAS quiz ID must be a positive integer')
    quiz = fetch_quiz(client, f'tst/{quiz_id}')
    response = client.session.get(f'https://ovidius.uni-tuebingen.de/goto.php/tst/{quiz_id}',
                                  timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if urlparse(response.url).netloc != 'ovidius.uni-tuebingen.de':
        raise AlmaParseError('ILIAS redirected outside the university host')
    action = parse_start_action(response.text, response.url, quiz_id)
    soup = BeautifulSoup(response.text, 'html.parser')
    region = soup.select_one('#il_center_col, #mainscrolldiv')
    review = {'quiz': serialize(quiz), 'visible_information': region.get_text(' ', strip=True) if region else None}
    review['review_sha256'] = hashlib.sha256(json.dumps(review, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review, action


def review_ilias_start(client, quiz_id: int) -> dict:
    review, _ = _preview(client, quiz_id)
    review['warning'] = 'Starting may consume an attempt and start a timer. ILIAS question support is limited and unverified live.'
    return review


def start_ilias_attempt(client, quiz_id: int, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review, action = _preview(client, quiz_id)
    if review['review_sha256'] != review_sha256:
        raise ValueError('ILIAS quiz information changed since review')
    try:
        response = client.session.get(action, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        return {'outcome': 'unknown', 'quiz_id': quiz_id,
                'message': 'The start request was sent; inspect ILIAS before retrying or proceeding.'}
    except Exception:
        raise AlmaParseError('ILIAS quiz start outcome is unknown; inspect ILIAS before retrying') from None

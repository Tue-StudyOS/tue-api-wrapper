"""Read supported questions from an existing ILIAS test attempt.

Resuming an attempt can restart its timer and update ILIAS attempt state.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError

HOST = 'ovidius.uni-tuebingen.de'
PLAYERS = {'ilTestPlayerFixedQuestionSetGUI', 'ilTestPlayerRandomQuestionSetGUI'}
KINDS = {'ilc_question_SingleChoice': 'single_choice', 'ilc_question_MultipleChoice': 'multiple_choice',
         'ilc_question_TextQuestion': 'text'}


def _player_url(target: str, quiz_id: int, commands: set[str], *, allow_final: bool = False) -> str:
    parsed = urlparse(target)
    query = parse_qs(parsed.query)
    allowed = {'baseClass', 'cmdNode', 'cmdClass', 'cmd', 'ref_id', 'sequence', 'pmode',
               'rtoken', 'active_id', 'fallbackCmd', 'finalization_confirmed'}
    if (parsed.scheme != 'https' or parsed.netloc != HOST or parsed.path != '/ilias.php'
            or set(query) - allowed
            or query.get('baseClass') != ['ilrepositorygui'] or len(query.get('cmdClass', [])) != 1
            or query['cmdClass'][0] not in PLAYERS or len(query.get('cmd', [])) != 1
            or query['cmd'][0] not in commands or query.get('ref_id') != [str(quiz_id)]
            or any(len(v) != 1 for v in query.values())
            or ('finalization_confirmed' in query and not (allow_final and query['finalization_confirmed'] == ['confirmed']))):
        raise AlmaParseError('ILIAS did not expose the expected test-player action')
    return target


def resume_action(html: str, page_url: str, quiz_id: int) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for node in soup.select('[data-action], a[href]'):
        url = urljoin(page_url, node.get('data-action') or node.get('href', ''))
        try:
            _player_url(url, quiz_id, {'resumePlayer'})
        except AlmaParseError:
            continue
        links.append(url)
    if len(set(links)) != 1:
        raise AlmaParseError('ILIAS did not expose one existing attempt to resume; no attempt was started')
    return links[0]


def question_form(html: str, page_url: str, quiz_id: int):
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.select_one('form#taForm')
    if not form or form.get('method', '').lower() != 'post':
        raise AlmaParseError('ILIAS did not return a supported in-progress question form')
    action = _player_url(urljoin(page_url, form.get('action', '')), quiz_id, {'post'})
    query = parse_qs(urlparse(action).query)
    if (query.get('fallbackCmd') != ['submitIntermediateSolution'] or not query.get('rtoken')
            or len(query.get('sequence', [])) != 1 or not query['sequence'][0].isdigit()):
        raise AlmaParseError('ILIAS question form has an unsupported action or sequence')
    candidates = [(node, KINDS[klass]) for node in form.select('[class]') for klass in node.get('class', []) if klass in KINDS]
    if len(candidates) != 1:
        raise AlmaParseError('ILIAS question type is not supported')
    node, kind = candidates[0]
    title = node.select_one('.ilc_qtitle_Title')
    if not title:
        raise AlmaParseError('ILIAS question text is missing')
    grouped = {}
    for control in node.select('input[name], textarea[name], select[name]'):
        typ = control.get('type', 'text').lower() if control.name == 'input' else control.name
        if typ == 'hidden' or control.has_attr('disabled'):
            continue
        name = control['name']
        supported = ((kind == 'single_choice' and typ == 'radio' and re.fullmatch(r'multiple_choice_result\d+', name))
                     or (kind == 'multiple_choice' and typ == 'checkbox' and re.fullmatch(r'multiple_choice_result_\d+', name))
                     or (kind == 'text' and typ == 'textarea' and name == 'TEXT'))
        if not supported:
            raise AlmaParseError('ILIAS question has an unsupported answer field')
        if kind == 'text' and name in grouped:
            raise AlmaParseError('ILIAS question contains duplicate text fields')
        field = grouped.setdefault(name, {'name': name, 'type': typ, 'value': None, 'options': []})
        if typ in {'radio', 'checkbox'}:
            label = node.find('label', attrs={'for': control.get('id')}) if control.get('id') else None
            field['options'].append({'value': control.get('value', 'on'),
                                     'label': label.get_text(' ', strip=True) if label else None,
                                     'selected': control.has_attr('checked')})
        else:
            field['value'] = control.get_text()
    locked = bool(node.find_parent(class_='readonly') or 'readonly' in node.get('class', []))
    if not grouped and not locked:
        raise AlmaParseError('ILIAS question has no supported editable answer fields')
    resources = []
    for item in node.select('a[href], img[src]'):
        url = urljoin(page_url, item.get('href') or item.get('src', ''))
        parsed = urlparse(url)
        if parsed.scheme in {'http', 'https'} and not any(
                key.casefold() in {'rtoken', 'sesskey', 'token'} for key in parse_qs(parsed.query)):
            resources.append({'kind': 'image' if item.name == 'img' else 'link', 'url': url,
                              'label': item.get('alt', '') if item.name == 'img' else item.get_text(' ', strip=True)})
    public = {'quiz_id': quiz_id, 'sequence': int(query['sequence'][0]),
              'question': {'kind': kind, 'text': title.get_text(' ', strip=True), 'editable': bool(grouped),
                           'fields': list(grouped.values()), 'displayed_answers': [
                               answer.get_text(' ', strip=True) for answer in node.select('.ilc_qanswer_Answer')],
                           'resources': resources},
              'warning': 'Resuming or viewing a question may update attempt state and restart a timer.'}
    return public, form, action


def parse_question(html: str, page_url: str, quiz_id: int) -> dict:
    public, _, _ = question_form(html, page_url, quiz_id)
    return public


def open_question(client, quiz_id: int):
    if isinstance(quiz_id, bool) or not isinstance(quiz_id, int) or quiz_id < 1:
        raise ValueError('ILIAS quiz ID must be a positive integer')
    origin = f'https://{HOST}/goto.php/tst/{quiz_id}'
    url = origin
    for _ in range(4):
        response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code == 200:
            break
        if response.status_code not in {302, 303}:
            raise AlmaParseError('ILIAS did not return the test overview')
        url = urljoin(response.url, response.headers.get('Location', ''))
        parsed, query = urlparse(url), parse_qs(urlparse(url).query)
        if (parsed.scheme != 'https' or parsed.netloc != HOST or parsed.path != '/ilias.php'
                or set(query) - {'baseClass', 'cmdNode', 'cmdClass', 'cmd', 'ref_id'}
                or query.get('baseClass') != ['ilrepositorygui'] or query.get('ref_id') != [str(quiz_id)]
                or query.get('cmdClass') not in (['ilObjTestGUI'], ['ILIAS\\Test\\Presentation\\TestScreenGUI'])
                or query.get('cmd', ['testScreen']) != ['testScreen'] or any(len(v) != 1 for v in query.values())):
            raise AlmaParseError('ILIAS overview redirected to an unsupported action')
    else:
        raise AlmaParseError('ILIAS test overview redirected too many times')
    url = resume_action(response.text, response.url, quiz_id)
    for _ in range(4):
        response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code == 200:
            return response.text, response.url
        if response.status_code not in {302, 303}:
            break
        url = _player_url(urljoin(response.url, response.headers.get('Location', '')), quiz_id, {'showQuestion'})
    raise AlmaParseError('ILIAS did not return the active question; inspect the attempt in ILIAS')


def fetch_question(client, quiz_id: int) -> dict:
    html, url = open_question(client, quiz_id)
    return parse_question(html, url, quiz_id)

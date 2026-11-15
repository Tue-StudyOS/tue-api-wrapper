"""Review and explicitly finish an existing Moodle quiz attempt."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


def parse_finish_form(html: str, page_url: str, attempt_id: int):
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.select_one('form#frm-finishattempt')
    table = soup.select_one('#region-main table')
    if not form or not table or form.get('method', '').lower() != 'post':
        raise AlmaParseError('Moodle did not return a supported quiz finish summary')
    action = urlparse(urljoin(page_url, form.get('action', '')))
    if (action.scheme != urlparse(page_url).scheme or action.netloc != urlparse(page_url).netloc
            or action.path != '/mod/quiz/processattempt.php'):
        raise AlmaParseError('Moodle finish form has an unsupported action')
    payload = {}
    for name, values in parse_qs(action.query, keep_blank_values=True).items():
        if len(values) != 1:
            raise AlmaParseError('Moodle finish form contains ambiguous fields')
        payload[name] = values[0]
    for node in form.select('input[type="hidden"][name]'):
        if node['name'] in payload:
            raise AlmaParseError('Moodle finish form contains duplicate fields')
        payload[node['name']] = node.get('value', '')
    if (payload.get('attempt') != str(attempt_id) or payload.get('finishattempt') != '1'
            or payload.get('timeup', '0') != '0' or not payload.get('sesskey')
            or form.select('textarea, select, input[type="checkbox"], input[type="radio"]')):
        raise AlmaParseError('Moodle finish form requires unsupported inputs')
    summary = table.get_text(' ', strip=True)
    if not summary:
        raise AlmaParseError('Moodle did not show an attempt summary')
    review = {'attempt_id': attempt_id, 'summary': summary}
    safe_fields = {k: v for k, v in payload.items() if k != 'sesskey'}
    review['review_sha256'] = hashlib.sha256(json.dumps({'summary': summary, 'fields': safe_fields},
                                         sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review, payload


def _prepare(client, attempt_id: int):
    if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
        raise ValueError('Attempt ID must be positive')
    url = f'{client.base_url}/mod/quiz/summary.php?attempt={attempt_id}'
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    parsed = urlparse(response.url)
    if (response.status_code != 200 or parsed.netloc != urlparse(client.base_url).netloc
            or parsed.path != '/mod/quiz/summary.php' or parse_qs(parsed.query).get('attempt') != [str(attempt_id)]):
        raise AlmaParseError('Moodle did not return the requested quiz summary')
    return parse_finish_form(response.text, response.url, attempt_id)


def review_finish(client, attempt_id: int) -> dict:
    review, _ = _prepare(client, attempt_id)
    review['warning'] = 'Finishing submits all answers for grading and may be irreversible.'
    return review


def finish_attempt(client, attempt_id: int, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review, payload = _prepare(client, attempt_id)
    if review['review_sha256'] != review_sha256:
        raise ValueError('Quiz summary changed since review')
    try:
        response = client.session.post(f'{client.base_url}/mod/quiz/processattempt.php', data=payload,
                                       timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code not in {200, 302, 303}:
            raise AlmaParseError('Unexpected finish response')
        url = f'{client.base_url}/mod/quiz/review.php?attempt={attempt_id}'
        result = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
        parsed = urlparse(result.url)
        if (result.status_code != 200 or parsed.netloc != urlparse(client.base_url).netloc
                or parsed.path != '/mod/quiz/review.php' or parse_qs(parsed.query).get('attempt') != [str(attempt_id)]):
            return {'outcome': 'unknown', 'attempt_id': attempt_id}
        soup = BeautifulSoup(result.text, 'html.parser')
        status = []
        for row in soup.select('#region-main table tr'):
            th, td = row.find('th'), row.find('td')
            if th and td and th.get_text(' ', strip=True).casefold() in {'state', 'status'}:
                status.append(td.get_text(' ', strip=True).casefold())
        confirmed = len(status) == 1 and status[0] in {'finished', 'beendet', 'abgeschlossen'}
        return {'outcome': 'finished' if confirmed else 'unknown', 'attempt_id': attempt_id}
    except Exception:
        raise AlmaParseError('Quiz finish outcome is unknown; inspect Moodle before retrying') from None

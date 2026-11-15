"""Opt-in unparsed forum and quiz pages for parser recovery."""
from __future__ import annotations

from .ilias_forum_threads import validate_forum_target, validate_thread_url


def raw_interaction(client, service: str, kind: str, target: str, *, page: int = 0) -> dict:
    if isinstance(page, bool) or not isinstance(page, int) or page < 0:
        raise ValueError('Page must be nonnegative')
    if service == 'moodle':
        paths = {'forum': ('/mod/forum/view.php', 'id'), 'discussion': ('/mod/forum/discuss.php', 'd'),
                 'quiz': ('/mod/quiz/view.php', 'id'), 'attempt': ('/mod/quiz/attempt.php', 'attempt')}
        if kind not in paths or not target.isascii() or not target.isdigit() or int(target) < 1:
            raise ValueError('Moodle resource requires a supported kind and positive numeric target')
        source = client.moodle.client
        path, param = paths[kind]
        suffix = f'&page={page}' if kind in {'forum', 'attempt'} else ''
        url = f'{source.base_url}{path}?{param}={target}{suffix}'
    elif service == 'ilias' and kind in {'forum', 'discussion'}:
        source = client.ilias.client
        if kind == 'forum':
            value = validate_forum_target(target)
            url = value if value.startswith('https://') else f'https://ovidius.uni-tuebingen.de/goto.php/{value}'
        else:
            url = validate_thread_url(target)
    else:
        raise ValueError('Unsupported interaction service or kind')
    response = source.session.get(url, timeout=source.timeout_seconds, allow_redirects=False)
    return {'service': service, 'kind': kind, 'status_code': response.status_code,
            'request_url': response.url, 'content_type': response.headers.get('Content-Type'),
            'location': response.headers.get('Location'), 'body': response.text, 'redirects_followed': False}

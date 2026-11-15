"""Review and explicitly publish ILIAS forum discussions or replies."""
from __future__ import annotations

import hashlib
import html as html_escape
import json
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .ilias_forum_threads import fetch_thread, validate_forum_target, validate_thread_url


def parse_editor(html: str, page_url: str, *, forum_id: str, mode: str,
                 thread_id: str | None = None, parent_id: str | None = None) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    forms = []
    for form in soup.select('form[method]'):
        target = urlparse(urljoin(page_url, form.get('action', '')))
        query = parse_qs(target.query)
        if (form['method'].lower() == 'post' and target.scheme == 'https'
                and target.netloc == 'ovidius.uni-tuebingen.de' and target.path == '/ilias.php'
                and query.get('cmd') == ['post'] and query.get('ref_id') == [forum_id]
                and (mode != 'reply' or (query.get('thr_pk') == [thread_id] and query.get('pos_pk') == [parent_id]))
                and query.get('rtoken') and form.select_one('textarea[name="message"]')):
            forms.append((form, target.geturl()))
    if len(forms) != 1:
        raise AlmaParseError('ILIAS did not return a supported forum editor')
    form, action = forms[0]
    command = 'cmd[addThread]' if mode == 'new' else 'cmd[savePost]'
    button = form.select_one(f'input[name="{command}"]')
    if not button or not form.select_one('input[name="subject"]'):
        raise AlmaParseError('ILIAS forum editor does not match the requested action')
    fields = {}
    for node in form.select('input[name]'):
        name, kind = node['name'], node.get('type', 'text').lower()
        if kind == 'hidden' or (kind == 'text' and name in {'alias', 'myCounter'}):
            if name in fields:
                raise AlmaParseError('ILIAS editor has duplicate fields')
            fields[name] = node.get('value', '')
        elif kind in {'file', 'submit'} or name == 'subject':
            continue
        else:
            raise AlmaParseError('ILIAS editor requires an unsupported field')
    if form.select('select, input[type="checkbox"], input[type="radio"]'):
        raise AlmaParseError('ILIAS editor requires an unsupported selection')
    fields[command] = button.get('value', '')
    editor = form.select_one('textarea[name="message"]')
    return {'action': action, 'fields': fields, 'rich_text': 'RTEditor' in editor.get('class', [])}


def _editor(client, mode: str, target: str, parent_id: str | None):
    thread_id = None
    if mode == 'new':
        forum = validate_forum_target(target)
        forum_id = forum.rstrip('/').split('/')[-1]
        url = f'https://ovidius.uni-tuebingen.de/goto.php/frm/{forum_id}'
    elif mode == 'reply':
        url = validate_thread_url(target)
        original = parse_qs(urlparse(url).query)
        forum_id, thread_id = original['ref_id'][0], original['thr_pk'][0]
        if not parent_id or not parent_id.isascii() or not parent_id.isdigit():
            raise ValueError('A numeric parent post ID is required for a reply')
    else:
        raise ValueError('Mode must be new or reply')
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if urlparse(response.url).netloc != 'ovidius.uni-tuebingen.de':
        raise AlmaParseError('ILIAS redirected outside the university host')
    soup = BeautifulSoup(response.text, 'html.parser')
    if mode == 'reply':
        rows = soup.select('#ilFrmPostList li.ilFrmPostRow')
        selected = []
        for row in rows:
            link = row.select_one('.ilFrmPostTitle a[href]')
            if link and parse_qs(urlparse(link['href']).query).get('pos_pk') == [parent_id]:
                selected.extend(row.select('button[data-action]'))
    else:
        selected = soup.select('button[data-action], a[data-action]')
    actions = []
    for node in selected:
        url = urljoin(response.url, node['data-action'])
        parsed, query = urlparse(url), parse_qs(urlparse(url).query)
        expected = 'createThread' if mode == 'new' else 'viewThread'
        if (parsed.scheme == 'https' and parsed.netloc == 'ovidius.uni-tuebingen.de' and parsed.path == '/ilias.php'
                and query.get('cmd') == [expected] and query.get('ref_id') == [forum_id]
                and (mode == 'new' or (query.get('action') == ['showreply'] and query.get('pos_pk') == [parent_id]
                                      and query.get('thr_pk') == [thread_id]))):
            actions.append(url)
    if len(actions) != 1:
        raise AlmaParseError('ILIAS does not offer an unambiguous forum editor')
    editor = client.session.get(actions[0], timeout=client.timeout_seconds, allow_redirects=False)
    editor.raise_for_status()
    if editor.status_code != 200:
        raise AlmaParseError('ILIAS did not open the forum editor')
    return parse_editor(editor.text, editor.url, forum_id=forum_id, mode=mode,
                        thread_id=thread_id, parent_id=parent_id), forum_id


def review_ilias_post(client, mode: str, target: str, subject: str, message: str, parent_id: str | None = None) -> dict:
    if not subject.strip() or not message.strip():
        raise ValueError('A subject and message are required')
    form, forum_id = _editor(client, mode, target, parent_id)
    review = {'mode': mode, 'target': target, 'forum_id': forum_id, 'parent_id': parent_id,
              'subject': subject, 'message': message, 'alias': form['fields'].get('alias', ''),
              'rich_text': form['rich_text']}
    review['review_sha256'] = hashlib.sha256(json.dumps(review, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review


def publish_ilias_post(client, mode: str, target: str, subject: str, message: str,
                       review_sha256: str, *, confirm: bool, parent_id: str | None = None) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    review = review_ilias_post(client, mode, target, subject, message, parent_id)
    if review['review_sha256'] != review_sha256:
        raise ValueError('Forum target or message changed since review')
    form, _ = _editor(client, mode, target, parent_id)
    if form['fields'].get('alias', '') != review['alias'] or form['rich_text'] != review['rich_text']:
        raise ValueError('ILIAS posting identity changed since review')
    form['fields']['subject'] = subject
    form['fields']['message'] = '<p>' + html_escape.escape(message).replace('\n', '<br>') + '</p>' if form['rich_text'] else message
    try:
        response = client.session.post(form['action'], data=form['fields'], timeout=client.timeout_seconds,
                                       allow_redirects=False)
        response.raise_for_status()
        location = urlparse(urljoin('https://ovidius.uni-tuebingen.de/', response.headers.get('Location', '')))
        query = parse_qs(location.query)
        post_id = query.get('pos_pk', [])
        if (response.status_code in {302, 303} and location.scheme == 'https'
                and location.netloc == 'ovidius.uni-tuebingen.de' and location.path == '/ilias.php'
                and query.get('cmd') == ['viewThread'] and query.get('ref_id') == [review['forum_id']]
                and (mode != 'reply' or query.get('thr_pk') == parse_qs(urlparse(target).query).get('thr_pk'))
                and len(post_id) == 1 and post_id[0].isdigit()):
            safe = {k: v[0] for k, v in query.items() if k in {
                'baseClass', 'cmdNode', 'cmdClass', 'cmd', 'ref_id', 'thr_pk', 'page', 'viewmode'} and len(v) == 1}
            thread_url = urlunparse((location.scheme, location.netloc, location.path, '', urlencode(safe), ''))
            thread = fetch_thread(client, validate_thread_url(thread_url))
            found = [p for p in thread.posts if p.id == post_id[0]]
            if (len(found) == 1 and found[0].subject.strip() == subject.strip()
                    and ' '.join(found[0].body.split()) == ' '.join(message.split())):
                return {'outcome': 'confirmed', 'post_id': post_id[0]}
        # A generic redirect is not a receipt.
        return {'outcome': 'unknown', 'message': 'Inspect the ILIAS forum to confirm the post before retrying.'}
    except Exception:
        raise AlmaParseError('Post outcome is unknown; inspect ILIAS before retrying') from None

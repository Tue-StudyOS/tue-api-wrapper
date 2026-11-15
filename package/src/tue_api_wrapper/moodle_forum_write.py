"""Review and post plain-text Moodle forum discussions or replies."""
from __future__ import annotations

import hashlib
import html as html_escape
import json
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_forums import fetch_discussion


def parse_post_form(html: str, page_url: str, *, mode: str, target: int) -> dict:
    if mode not in {'new', 'reply'}:
        raise ValueError('Mode must be new or reply')
    soup = BeautifulSoup(html, 'html.parser')
    forms = []
    for form in soup.select('form[method]'):
        url = urlparse(urljoin(page_url, form.get('action', '')))
        if (form['method'].lower() == 'post' and url.scheme == 'https'
                and url.netloc == urlparse(page_url).netloc and url.path == '/mod/forum/post.php'
                and not url.query and form.select_one('textarea[name="message[text]"]')):
            forms.append(form)
    if len(forms) != 1:
        raise AlmaParseError('Moodle did not expose one recognizable forum posting form')
    form = forms[0]
    data = {}
    for node in form.select('input[type="hidden"][name]'):
        if node['name'] in data:
            raise AlmaParseError('Moodle forum form contains duplicate fields')
        data[node['name']] = node.get('value', '')
    if (not data.get('sesskey') or not data.get('forum', '').isdigit()
            or (mode == 'reply' and data.get('parent') != str(target))
            or (mode == 'new' and data.get('parent', '0') != '0')
            or data.get('message[format]') not in {'1', '2'}):
        raise AlmaParseError('Moodle forum form does not match the requested action')
    if not form.select_one('input[name="subject"]'):
        raise AlmaParseError('Moodle forum form has no subject field')
    for control in form.select('input[type="checkbox"][name]'):
        if control['name'] != 'discussionsubscribe':
            raise AlmaParseError('Moodle forum form requires an unsupported choice')
        if control.has_attr('checked'):
            data['discussionsubscribe'] = control.get('value', '1')
    for select in form.select('select[name]'):
        if select['name'] != 'tags[]' or select.select('option[selected][value]:not([value=""])'):
            raise AlmaParseError('Moodle forum form requires an unsupported selection')
    button = form.select_one('input[type="submit"][name="submitbutton"]')
    if button:
        data['submitbutton'] = button.get('value', '')
    return data


def _form(client, mode: str, target: int):
    if isinstance(target, bool) or not isinstance(target, int) or target < 1:
        raise ValueError('Forum or post identifier must be a positive integer')
    if mode == 'new':
        url = f'{client.base_url}/mod/forum/view.php?id={target}'
        expected_path, param = '/mod/forum/view.php', 'id'
    elif mode == 'reply':
        url = f'{client.base_url}/mod/forum/post.php?reply={target}'
        expected_path, param = '/mod/forum/post.php', 'reply'
    else:
        raise ValueError('Mode must be new or reply')
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    parsed = urlparse(response.url)
    if (response.status_code != 200 or parsed.netloc != urlparse(client.base_url).netloc
            or parsed.path != expected_path or parse_qs(parsed.query).get(param) != [str(target)]):
        raise AlmaParseError('Moodle did not return the requested forum form')
    return parse_post_form(response.text, response.url, mode=mode, target=target)


def review_post(client, mode: str, target: int, subject: str, message: str) -> dict:
    if not subject.strip() or not message.strip():
        raise ValueError('A subject and message are required')
    form = _form(client, mode, target)
    context = {k: form.get(k) for k in ('forum', 'discussion', 'parent', 'groupid', 'discussionsubscribe')}
    review = {'mode': mode, 'target': target, 'subject': subject, 'message': message, 'context': context}
    review['review_sha256'] = hashlib.sha256(json.dumps(review, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return review


def publish_post(client, mode: str, target: int, subject: str, message: str, review_sha256: str, *, confirm: bool) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    reviewed = review_post(client, mode, target, subject, message)
    if reviewed['review_sha256'] != review_sha256:
        raise ValueError('Forum target or message changed since review')
    form = _form(client, mode, target)
    if any(form.get(k) != v for k, v in reviewed['context'].items()):
        raise ValueError('Moodle forum context changed since review')
    form['subject'] = subject
    form['message[text]'] = '<p>' + html_escape.escape(message).replace('\n', '<br>') + '</p>' if form['message[format]'] == '1' else message
    try:
        response = client.session.post(f'{client.base_url}/mod/forum/post.php', data=form,
                                       timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        location = urlparse(urljoin(client.base_url, response.headers.get('Location', '')))
        ids = parse_qs(location.query).get('d', [])
        if (response.status_code not in {302, 303} or location.netloc != urlparse(client.base_url).netloc
                or location.scheme != 'https' or location.path != '/mod/forum/discuss.php' or len(ids) != 1
                or not ids[0].isdigit() or not location.fragment.startswith('p') or not location.fragment[1:].isdigit()):
            return {'outcome': 'unknown', 'message': 'Inspect Moodle before retrying; the post may have been sent.'}
        discussion = fetch_discussion(client, int(ids[0]))
        posts = [p for p in discussion.posts if p.id == location.fragment[1:]]
        verified = len(posts) == 1 and ' '.join(posts[0].body.split()) == ' '.join(message.split())
        return {'outcome': 'confirmed' if verified else 'unknown', 'discussion_id': int(ids[0]),
                'post_id': location.fragment[1:]}
    except Exception:
        raise AlmaParseError('Post outcome is unknown; inspect Moodle before retrying') from None

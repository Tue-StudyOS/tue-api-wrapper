"""Read visible ILIAS forum posts without executing post actions."""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_forums import ForumLink


@dataclass(frozen=True)
class IliasForumPost:
    id: str
    subject: str
    author_and_date: str | None
    body: str
    links: tuple[ForumLink, ...]


@dataclass(frozen=True)
class IliasForumThread:
    source_url: str
    title: str
    posts: tuple[IliasForumPost, ...]


def validate_forum_target(target: str) -> str:
    if re.fullmatch(r'frm/[0-9]+', target):
        return target
    parsed = urlparse(target)
    if (parsed.scheme == 'https' and parsed.netloc == 'ovidius.uni-tuebingen.de'
            and re.fullmatch(r'/goto.php/frm/[0-9]+/?', parsed.path) and not parsed.query):
        return target
    raise AlmaParseError('Expected an ILIAS forum target such as frm/123')


def validate_thread_url(target: str) -> str:
    url = urlparse(target)
    params = parse_qs(url.query)
    allowed = {'baseClass', 'cmdNode', 'cmdClass', 'cmd', 'ref_id', 'thr_pk', 'page', 'viewmode'}
    if (url.scheme != 'https' or url.netloc != 'ovidius.uni-tuebingen.de' or url.path != '/ilias.php'
            or set(params) - allowed or any(len(v) != 1 for v in params.values())
            or params.get('baseClass') != ['ilrepositorygui'] or params.get('cmdClass') != ['ilObjForumGUI']
            or params.get('cmd') != ['viewThread'] or len(params.get('ref_id', [])) != 1
            or len(params.get('thr_pk', [])) != 1
            or not params['ref_id'][0].isdigit() or not params['thr_pk'][0].isdigit()):
        raise AlmaParseError('Expected an ILIAS viewThread URL on the university host')
    return target


def fetch_thread(client, target: str) -> IliasForumThread:
    target = validate_thread_url(target)
    response = client.session.get(target, timeout=client.timeout_seconds, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise AlmaParseError('ILIAS did not return the requested discussion')
    return parse_thread(response.text, response.url)


def parse_thread(html: str, page_url: str) -> IliasForumThread:
    soup = BeautifulSoup(html, 'html.parser')
    container, heading = soup.select_one('#ilFrmPostList'), soup.select_one('h1')
    if not container or not heading:
        raise AlmaParseError('ILIAS did not return a recognizable discussion')
    posts = []
    for item in container.select('li.ilFrmPostRow'):
        title = item.select_one('.ilFrmPostTitle a[href]')
        body = item.select_one('.ilFrmPostContent')
        if not title or not body:
            raise AlmaParseError('ILIAS discussion contains an unrecognized post')
        ids = parse_qs(urlparse(urljoin(page_url, title['href'])).query).get('pos_pk', [])
        if len(ids) != 1 or not ids[0].isdigit():
            raise AlmaParseError('ILIAS discussion post has no recognizable identifier')
        author = item.select_one('.ilFrmPostHeader .small')
        links = tuple(ForumLink(a.get_text(' ', strip=True), urljoin(page_url, a['href']))
                      for a in body.select('a[href]') if urlparse(urljoin(page_url, a['href'])).scheme in {'https', 'http'})
        posts.append(IliasForumPost(ids[0], title.get_text(' ', strip=True),
                                    author.get_text(' ', strip=True) if author else None,
                                    body.get_text(' ', strip=True), links))
    if not posts:
        raise AlmaParseError('ILIAS discussion has no recognizable posts')
    return IliasForumThread(page_url, heading.get_text(' ', strip=True), tuple(posts))

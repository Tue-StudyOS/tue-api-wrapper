"""Read Moodle forum discussion lists and posts visible to the account."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


@dataclass(frozen=True)
class ForumLink:
    label: str
    url: str


@dataclass(frozen=True)
class MoodleDiscussionSummary:
    title: str
    url: str
    author: str | None
    replies: str | None


@dataclass(frozen=True)
class MoodleForum:
    forum_id: int
    source_url: str
    title: str
    discussions: tuple[MoodleDiscussionSummary, ...]
    next_url: str | None


@dataclass(frozen=True)
class MoodleForumPost:
    id: str
    parent_id: str | None
    subject: str | None
    author: str | None
    posted_at: str | None
    body: str
    attachments: tuple[ForumLink, ...]


@dataclass(frozen=True)
class MoodleDiscussion:
    discussion_id: int
    source_url: str
    title: str
    posts: tuple[MoodleForumPost, ...]


def _fetch(client, path: str, param: str, ident: int, *, page: int | None = None):
    if isinstance(ident, bool) or not isinstance(ident, int) or ident < 1:
        raise ValueError('Moodle forum identifier must be a positive integer')
    if page is not None and (isinstance(page, bool) or not isinstance(page, int) or page < 0):
        raise ValueError('Moodle forum page must be a nonnegative integer')
    suffix = f'&page={page}' if page is not None else ''
    html, url = client._get_authenticated_page(f'{client.base_url}{path}?{param}={ident}{suffix}')
    parsed = urlparse(url)
    if (parsed.netloc != urlparse(client.base_url).netloc or parsed.path != path
            or parse_qs(parsed.query).get(param) != [str(ident)]):
        raise AlmaParseError('Moodle did not return the requested forum page')
    return html, url


def fetch_forum(client, forum_id: int, *, page: int = 0):
    html, url = _fetch(client, '/mod/forum/view.php', 'id', forum_id, page=page)
    return parse_forum(html, url, forum_id)


def fetch_discussion(client, discussion_id: int):
    html, url = _fetch(client, '/mod/forum/discuss.php', 'd', discussion_id)
    return parse_discussion(html, url, discussion_id)


def _title(soup):
    heading = soup.select_one('#page-header h1, #region-main h1')
    if not heading:
        raise AlmaParseError('Moodle forum page has no recognizable title')
    return heading.get_text(' ', strip=True)


def parse_forum(html: str, page_url: str, forum_id: int) -> MoodleForum:
    soup = BeautifulSoup(html, 'html.parser')
    title = _title(soup)
    table = soup.select_one('#region-main .discussion-list')
    if not table and not soup.select_one('#region-main .forumnodiscuss'):
        raise AlmaParseError('Moodle did not return a recognizable forum discussion list')
    items = []
    for row in table.select('tr.discussion') if table else []:
        link = row.select_one('.topic a[href*="discuss.php"]')
        if not link:
            raise AlmaParseError('Moodle forum discussion has no recognizable link')
        author, replies = row.select_one('.author'), row.select_one('.replies')
        items.append(MoodleDiscussionSummary(link.get_text(' ', strip=True), urljoin(page_url, link['href']),
                                            author.get_text(' ', strip=True) if author else None,
                                            replies.get_text(' ', strip=True) if replies else None))
    next_link = soup.select_one('#region-main a[rel="next"][href]')
    next_url = urljoin(page_url, next_link['href']) if next_link else None
    if next_url and urlparse(next_url).netloc != urlparse(page_url).netloc:
        raise AlmaParseError('Moodle forum pagination points to another host')
    return MoodleForum(forum_id, page_url, title, tuple(items), next_url)


def parse_discussion(html: str, page_url: str, discussion_id: int) -> MoodleDiscussion:
    soup = BeautifulSoup(html, 'html.parser')
    title = _title(soup)
    articles = soup.select('#region-main article[data-region="post"][data-post-id]')
    if not articles:
        raise AlmaParseError('Moodle did not return recognizable discussion posts')
    posts = []
    for article in articles:
        header = article.select_one('header')
        body = article.select_one('.post-content-container')
        if not header or not body:
            raise AlmaParseError('Moodle discussion contains an unrecognized post')
        heading, author, time = header.select_one('h3'), header.select_one('a[href*="/user/"]'), header.select_one('time')
        parent = article.find_parent('article', attrs={'data-region': 'post'})
        links = tuple(ForumLink(a.get_text(' ', strip=True), urljoin(page_url, a['href']))
                      for a in body.select('a[href]') if urlparse(urljoin(page_url, a['href'])).scheme in {'http', 'https'})
        posts.append(MoodleForumPost(article['data-post-id'], parent.get('data-post-id') if parent else None,
                                    heading.get_text(' ', strip=True) if heading else None,
                                    author.get_text(' ', strip=True) if author else None,
                                    time.get('datetime') if time else None, body.get_text(' ', strip=True), links))
    return MoodleDiscussion(discussion_id, page_url, title, tuple(posts))

from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup, Tag

from .advising_models import AdvisingField, AdvisingLink, AdvisingPage, AdvisingTopic
from .config import AlmaParseError, DEFAULT_TIMEOUT_SECONDS

DEFAULT_ADVISING_URL = (
    'https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/'
    'fachbereiche/informatik/lehrstuehle/kommunikationsnetze/staff/paul-stahl/'
)


class AdvisingClient:
    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT_SECONDS, session: requests.Session | None = None) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch(self, url: str = DEFAULT_ADVISING_URL) -> AdvisingPage:
        html, final_url = self.fetch_html(url)
        return parse_advising_page(html, source_url=final_url)

    def fetch_html(self, url: str) -> tuple[bytes, str]:
        # Validate every redirect before making the next request.
        for _ in range(6):
            _validate_url(url)
            response = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            if response.is_redirect:
                url = urljoin(url, response.headers['Location'])
                continue
            response.raise_for_status()
            return response.content, url
        raise AlmaParseError('The advising page redirected too many times.')


def _validate_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        valid = (parts.scheme == 'https' and parts.hostname in {'uni-tuebingen.de', 'db.cs.uni-tuebingen.de'}
                 and parts.port in (None, 443) and not parts.username and not parts.password)
    except ValueError:
        valid = False
    if not valid:
        raise AlmaParseError('The advising page must use HTTPS on uni-tuebingen.de or db.cs.uni-tuebingen.de.')


def parse_advising_page(html: str | bytes, *, source_url: str) -> AdvisingPage:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main')
    if not isinstance(main, Tag):
        raise AlmaParseError('The advising page has no main content.')
    sections: dict[str, Tag] = {}
    contact_block = None
    for heading in main.find_all(['h1', 'h2', 'h3']):
        text = _text(heading)
        block = heading.find_parent(class_='ut-box__block')
        if not isinstance(block, Tag):
            continue
        if text.casefold() == 'studienfachberatung' and contact_block is None:
            contact_block = block
        if re.fullmatch(r'ich kann (?:ihnen )?(?:nicht )?helfen bei', text, re.I):
            sections['cannot_help' if 'nicht' in text.casefold() else 'can_help'] = block
    parsed = {key: _topics(block, source_url) for key, block in sections.items()}
    for paragraph in main.find_all('p'):
        text = _text(paragraph)
        if re.fullmatch(r'ich kann (?:ihnen )?(?:nicht )?helfen bei', text, re.I):
            table = paragraph.find_next_sibling('table')
            if isinstance(table, Tag):
                key = 'cannot_help' if 'nicht' in text.casefold() else 'can_help'
                parsed[key] = _topics(table, source_url)
    if not parsed:
        raise AlmaParseError('No supported advising responsibility tables were found on this page.')
    if any(not entries for entries in parsed.values()):
        raise AlmaParseError('An advising responsibility table is missing or empty.')
    name = None
    contact: list[AdvisingField] = []
    if contact_block is not None:
        paragraph = contact_block.select_one('.ut-box__text > p')
        name = _text(paragraph) or None
        table = contact_block.find('table')
        if isinstance(table, Tag):
            for cells in _rows(table):
                contact.append(AdvisingField(_text(cells[0]), _text(cells[1]), _links(cells[1], source_url)))
    if contact_block is None and urlsplit(source_url).hostname == 'db.cs.uni-tuebingen.de':
        profile = main.select_one('.ut-grid__col-2 .ut-box__text')
        if isinstance(profile, Tag):
            name = _text(profile.find('strong')) or None
            contact.append(AdvisingField('Kontakt', _text(profile), _links(profile, source_url)))
    title = _text(soup.title).split('|')[0].strip() if soup.title else ''
    return AdvisingPage(source_url, title, name, tuple(contact), parsed.get('can_help', ()), parsed.get('cannot_help', ()))


def _topics(block: Tag, source_url: str) -> tuple[AdvisingTopic, ...]:
    table = block if block.name == 'table' else block.find('table')
    if not isinstance(table, Tag):
        return ()
    return tuple(AdvisingTopic(_text(cells[0]), _text(cells[1]), _links(cells[1], source_url))
                 for cells in _rows(table) if _text(cells[0]) and _text(cells[1]))


def _rows(table: Tag):
    for row in table.find_all('tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) == 2:
            yield cells


def _links(node: Tag, base_url: str) -> tuple[AdvisingLink, ...]:
    links = []
    for link in node.find_all('a'):
        href = str(link.get('href', ''))
        token = link.get('data-mailto-token')
        if token:
            try:
                vector = int(str(link.get('data-mailto-vector', '0')))
                href = ''.join(_shift_mail_char(char, -vector) for char in str(token))
            except ValueError:
                continue
        if href and href != '#' and urlsplit(href).scheme.lower() in ('', 'https', 'http', 'mailto', 'tel'):
            links.append(AdvisingLink(_text(link), urljoin(base_url, href)))
    return tuple(links)


def _text(node: Tag | None) -> str:
    return ' '.join(node.get_text(' ', strip=True).split()) if node else ''


def _shift_mail_char(char: str, offset: int) -> str:
    value = ord(char)
    for lower, upper in ((43, 58), (64, 90), (97, 122)):
        if lower <= value <= upper:
            return chr(lower + (value - lower + offset) % (upper - lower + 1))
    return char

from __future__ import annotations

import re
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from .advising_client import _links, _text, _validate_url
from .advising_discovery_models import AdvisingDiscoveryPage, AdvisingPassage
from .config import AlmaParseError


def parse_discovery_page(html: bytes | str, url: str, discovered_from: str | None):
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main')
    if not isinstance(main, Tag):
        raise AlmaParseError('The advising page has no main content.')
    for hidden in main.select('[style*="display:none"], [style*="display: none"]'):
        hidden.decompose()
    title = _text(soup.title).split('|')[0].strip() if soup.title else ''
    page = AdvisingDiscoveryPage(url, title, discovered_from)
    passages = []
    headings: dict[int, str] = {}
    consumed: set[int] = set()
    for node in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'tr']):
        if id(node) in consumed:
            continue
        if node.find_parent(['nav', 'table']) and node.name != 'tr':
            continue
        if node.name.startswith('h'):
            level = int(node.name[1])
            headings = {n: value for n, value in headings.items() if n < level}
            headings[level] = _text(node)
            continue
        if node.name == 'li' and node.find_parent('li'):
            continue
        if node.name == 'p' and node.find_parent('li'):
            continue
        if node.name == 'p' and 'ut-teaser' in node.get('class', []) and 'studienfachberatung' in _text(node).casefold():
            group = [node]
            for sibling in node.find_next_siblings():
                if sibling.name != 'p' or 'ut-teaser' in sibling.get('class', []):
                    break
                group.append(sibling)
                consumed.add(id(sibling))
            if len(group) > 1:
                section = ' / '.join(value for level, value in sorted(headings.items()) if level > 1)
                text = ' — '.join(_text(part) for part in group if _text(part))
                links = tuple(link for part in group for link in _links(part, url))
                passages.append(AdvisingPassage(url, title, section, 'directory_contact', text, links))
                continue
        if node.name == 'tr':
            cells = node.find_all('td', recursive=False)
            if not cells:
                continue
            text = ' — '.join(_text(cell) for cell in cells if _text(cell))
            kind = 'table_row'
        else:
            text = _text(node)
            kind = 'list_item' if node.name == 'li' else 'paragraph'
            if node.name == 'p' and re.fullmatch(r'ich kann (?:ihnen )?(?:nicht )?helfen bei', text, re.I):
                headings = {n: value for n, value in headings.items() if n < 2}
                headings[2] = text
                continue
        if node.name == 'tr' and re.search(r'ich kann (?:ihnen )?nicht helfen bei', ' '.join(headings.values()), re.I):
            kind = 'cannot_help'
        elif node.name == 'tr' and re.search(r'ich kann (?:ihnen )?helfen bei', ' '.join(headings.values()), re.I):
            kind = 'can_help'
        if not text:
            continue
        section = ' / '.join(value for level, value in sorted(headings.items()) if level > 1)
        passages.append(AdvisingPassage(url, title, section, kind, text, _links(node, url)))
    return page, tuple(passages), _candidates(main, url)


def _candidates(main: Tag, base_url: str) -> tuple[tuple[str, str], ...]:
    candidates = []
    seen = set()
    for link in main.find_all('a', href=True):
        href = str(link['href'])
        if not href or href.startswith(('#', 'mailto:', 'tel:')):
            continue
        url = urldefrag(urljoin(base_url, href))[0]
        try:
            _validate_url(url)
        except AlmaParseError:
            continue
        parts = urlsplit(url)
        if (url == urldefrag(base_url)[0] or url in seen or parts.query
                or re.search(r'\.(?:pdf|docx?|xlsx?|pptx?|zip)$', parts.path, re.I)):
            continue
        context_node = link.find_parent(class_='ut-text-media__text') or link.parent
        context = _text(context_node)[:2000] if isinstance(context_node, Tag) else ''
        # Follow explicit advising/FAQ links and university short links from the directory.
        label = _text(link)
        if not re.search(r'beratung|beratende|ansprech|faq|/de/\d+|/anlaufstellen-nach-thema/', f'{url} {label}', re.I):
            continue
        seen.add(url)
        candidates.append((url, f'{label} {context}'))
    return tuple(candidates)

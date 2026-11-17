from __future__ import annotations

import re
from threading import Lock

from .advising_client import AdvisingClient, DEFAULT_ADVISING_URL
from .advising_crawler import crawl_advising
from .advising_discovery_models import AdvisingIndex, AdvisingSearchResponse
from .advising_index_cache import AdvisingIndexCache
from .config import AlmaParseError

DIRECTORY_URL = 'https://uni-tuebingen.de/de/92'
SEEDS = (
    DIRECTORY_URL,
    'https://uni-tuebingen.de/studium/beratung-und-info/anlaufstellen-nach-thema/',
    'https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/studium/studierende/personen-und-kontakte/studienberatung/',
    'https://uni-tuebingen.de/fakultaeten/wirtschafts-und-sozialwissenschaftliche-fakultaet/faecher/fachbereich-sozialwissenschaften/erziehungswissenschaft/studium/studienberatung-faq/ansprechpartnerinnen/',
    DEFAULT_ADVISING_URL,
    'https://db.cs.uni-tuebingen.de/studienfachberatung/',
)


def _fetch(url: str):
    client = AdvisingClient()
    try:
        return client.fetch_html(url)
    finally:
        client.session.close()


class AdvisingDiscovery:
    def __init__(self, fetcher=None, cache: AdvisingIndexCache | None = None):
        self.fetcher = fetcher or _fetch
        self.cache = cache if cache is not None else (AdvisingIndexCache() if fetcher is None else None)
        self._snapshot: AdvisingIndex | None = None
        self._lock = Lock()

    def search(self, query: str, *, limit: int = 20) -> AdvisingSearchResponse:
        query = query.strip()
        if len(query) < 2 or len(query) > 200 or not _words(query):
            raise AlmaParseError('Enter an advising topic or degree with 2 to 200 characters, including a letter or number.')
        if not 1 <= limit <= 100:
            raise AlmaParseError('The advising search limit must be between 1 and 100.')
        return self._response(self._index(), query, limit)

    def discover(self) -> AdvisingSearchResponse:
        return self._response(self._index(), '', 0)

    def refresh(self) -> AdvisingSearchResponse:
        with self._lock:
            index = self._refresh()
        return self._response(index, '', 0)

    def _index(self) -> AdvisingIndex:
        with self._lock:
            index = self.cache.load() if self.cache else self._snapshot
            return index if index is not None else self._refresh()

    def _refresh(self) -> AdvisingIndex:
        index = crawl_advising(SEEDS, self.fetcher)
        if self.cache:
            self.cache.save(index)
        self._snapshot = index
        return index

    @staticmethod
    def _response(index: AdvisingIndex, query: str, limit: int) -> AdvisingSearchResponse:
        words = _words(query)
        matches = [(score, passage) for passage in index.passages
                   if _is_advising_context(passage.page_title, passage.section)
                   and (score := _score(words, passage.text, passage.section)) > 0]
        matches.sort(key=lambda item: (-item[0], item[1].page_title, item[1].section))
        return AdvisingSearchResponse(
            query=query, pages=index.pages, results=tuple(p for _, p in matches[:limit]), errors=index.errors,
            pages_skipped=index.pages_skipped, results_truncated=len(matches) > limit,
            refreshed_at=index.refreshed_at, pages_attempted=index.pages_attempted,
            links_beyond_depth=index.links_beyond_depth, seed_links_discovered=index.seed_links_discovered,
            seed_links_attempted=index.seed_links_attempted,
        )


def _words(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r'\w+', text.casefold()))


def _score(words: tuple[str, ...], *fields: str) -> int:
    if not words:
        return 0
    text = ' '.join(fields).casefold()
    if not all(word in text for word in words):
        return 0
    return sum(3 if word in fields[0].casefold() else 1 for word in words)


def _is_advising_context(title: str, section: str) -> bool:
    return bool(re.search(r'berat|ansprech|faq|helfen|studium|prüfungsamt|praktikum|ba[fö]g',
                          f'{title} {section}', re.I))

from __future__ import annotations

import pytest

from tue_api_wrapper import advising_discovery
from tue_api_wrapper.advising_crawler import crawl_advising
from tue_api_wrapper.advising_discovery import AdvisingDiscovery
from tue_api_wrapper.advising_index_cache import AdvisingIndexCache
from tue_api_wrapper.config import AlmaParseError, AlmaServiceUnavailableError

BASE = 'https://uni-tuebingen.de/'


def page(body):
    return f'<title>Studienberatung</title><main><h2>Beratung</h2>{body}</main>'


def test_crawls_all_first_level_links_before_second_level():
    seed = BASE + 'seed'
    links = ''.join(f'<a href="/de/{i}">Beratung</a>' for i in range(120))
    pages = {seed: page(links)}
    pages.update({BASE + f'de/{i}': page(f'<p>Recognition {i}</p><a href="/de/second-{i}">Beratung</a>')
                  for i in range(120)})
    pages.update({BASE + f'de/second-{i}': page('<p>Second level</p>') for i in range(120)})
    seen = []
    def fetch(url):
        seen.append(url)
        return pages[url], url
    index = crawl_advising((seed,), fetch, max_pages=125)
    assert index.seed_links_discovered == index.seed_links_attempted == 120
    assert index.pages_attempted == 125
    assert index.pages_skipped == 116
    assert len(index.pages) == 125
    assert all(BASE + f'de/{i}' in seen for i in range(120))


def test_reports_links_beyond_depth_and_deduplicates_cycles():
    seed, child, grandchild = (BASE + name for name in ('seed', 'de/1', 'de/2'))
    sources = {seed: page('<a href="/de/1">Beratung</a>'),
               child: page('<a href="/de/2">FAQ</a>'),
               grandchild: page('<a href="/de/1">FAQ</a><a href="/de/3">FAQ</a>')}
    index = crawl_advising((seed,), lambda url: (sources[url], url))
    assert index.pages_attempted == 3
    assert index.links_beyond_depth == 1
    assert index.pages_skipped == 0


def test_index_persists_and_explicit_refresh_updates_it(tmp_path, monkeypatch):
    seed = BASE + 'seed'
    monkeypatch.setattr(advising_discovery, 'SEEDS', (seed,))
    state = {'text': 'Anerkennung', 'calls': 0}
    def fetch(url):
        state['calls'] += 1
        return page(f'<p>{state["text"]}</p>'), url
    cache = AdvisingIndexCache(tmp_path / 'index.json')
    service = AdvisingDiscovery(fetcher=fetch, cache=cache)
    first = service.search('Anerkennung')
    assert len(first.results) == 1 and state['calls'] == 1
    state['text'] = 'Anrechnung'
    reopened = AdvisingDiscovery(fetcher=fetch, cache=cache)
    assert len(reopened.search('Anerkennung').results) == 1
    assert state['calls'] == 1
    reopened.refresh()
    assert len(reopened.search('Anrechnung').results) == 1
    assert state['calls'] == 2


def test_failed_refresh_preserves_existing_index(tmp_path, monkeypatch):
    monkeypatch.setattr(advising_discovery, 'SEEDS', (BASE + 'seed',))
    cache = AdvisingIndexCache(tmp_path / 'index.json')
    service = AdvisingDiscovery(fetcher=lambda url: (page('<p>Anerkennung</p>'), url), cache=cache)
    first = service.refresh()
    def fail(_url):
        raise OSError('offline')
    service.fetcher = fail
    with pytest.raises(AlmaServiceUnavailableError):
        service.refresh()
    assert service.search('Anerkennung').refreshed_at == first.refreshed_at


def test_invalid_index_is_not_silently_discarded(tmp_path):
    path = tmp_path / 'index.json'
    path.write_text('not json')
    with pytest.raises(AlmaParseError, match='invalid'):
        AdvisingIndexCache(path).load()


def test_primary_directory_failure_does_not_replace_index(tmp_path, monkeypatch):
    seed, secondary = BASE + 'seed', BASE + 'secondary'
    monkeypatch.setattr(advising_discovery, 'SEEDS', (seed, secondary))
    cache = AdvisingIndexCache(tmp_path / 'index.json')
    service = AdvisingDiscovery(fetcher=lambda url: (page('<p>Anerkennung</p>'), url), cache=cache)
    first = service.refresh()
    def fetch(url):
        if url == seed:
            raise OSError('directory unavailable')
        return page('<p>other page</p>'), url
    service.fetcher = fetch
    with pytest.raises(AlmaServiceUnavailableError, match='primary advising directory'):
        service.refresh()
    assert service.search('Anerkennung').refreshed_at == first.refreshed_at


def test_discovery_skips_document_links():
    from tue_api_wrapper.advising_discovery_html import parse_discovery_page
    html = page('<a href="/beratung.pdf">PDF</a><a href="/beratung/">Page</a>')
    _, _, candidates = parse_discovery_page(html, BASE, None)
    assert [url for url, _ in candidates] == [BASE + 'beratung/']

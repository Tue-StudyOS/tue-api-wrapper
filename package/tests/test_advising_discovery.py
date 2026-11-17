from __future__ import annotations

import pytest

from tue_api_wrapper import advising_discovery
from tue_api_wrapper.advising_discovery import AdvisingDiscovery
from tue_api_wrapper.advising_discovery_html import parse_discovery_page
from tue_api_wrapper.config import AlmaParseError

BASE = 'https://uni-tuebingen.de/'
DIRECTORY = '''<title>Studienfachberatung | Uni</title><main>
<div class="ut-text-media__text"><header><h2>Informatik</h2></header>
<p>Studienfachberatung Computer Science</p><p>Paul Stahl <a href="/de/123">Bürozeiten</a></p></div>
<a href="https://example.org/beratung">outside</a></main>'''
FAQ = '''<title>Studienberatung FAQ | Uni</title><main>
<h2>Mit welchen Fragen wende ich mich an die Studienfachberatung?</h2>
<ul><li>Anerkennung von Studienleistungen</li><li>Studienverlauf</li></ul>
<h2>Wer ist für meinen Studiengang zuständig?</h2><h4>Master Bildung</h4>
<p>Flora Petrik ist zuständig. <a href="/person/">Kontakt</a></p></main>'''
OVERVIEW = '''<title>Studienberatung Informatik | Uni</title><main><h2>Beratung durch Mitarbeiter</h2>
<table><tr><th>Studienfach</th><th>Berater</th></tr><tr><td>Informatik</td>
<td><a href="/paul/">Paul Stahl</a></td></tr></table></main>'''
LEGACY = '''<title>Database Systems | Studienfachberatung</title><main>
<p><strong>Ich kann helfen bei</strong></p><table><tr><td>Anerkennung</td><td>Modulbeschreibung beilegen</td></tr></table>
<p>Ich kann Ihnen <strong>nicht</strong> helfen bei</p><table><tr><td>Kursanmeldung</td><td><a href="mailto:other@uni-tuebingen.de">Andere Beratung</a></td></tr></table>
</main>'''


def test_extracts_directory_faq_tables_and_legacy_responsibilities():
    _, directory, links = parse_discovery_page(DIRECTORY, BASE, None)
    assert directory[1].section == 'Informatik'
    assert links[0][0] == BASE + 'de/123'
    assert all('example.org' not in link[0] for link in links)
    _, faq, _ = parse_discovery_page(FAQ, BASE, None)
    assert next(p for p in faq if 'Anerkennung' in p.text).kind == 'list_item'
    assert next(p for p in faq if 'Flora' in p.text).section.endswith('Master Bildung')
    _, overview, _ = parse_discovery_page(OVERVIEW, BASE, None)
    assert overview[0].text == 'Informatik — Paul Stahl'
    assert overview[0].links[0].url == BASE + 'paul/'
    _, legacy, _ = parse_discovery_page(LEGACY, BASE, None)
    assert [p.kind for p in legacy] == ['can_help', 'cannot_help']
    assert legacy[1].links[0].url == 'mailto:other@uni-tuebingen.de'


def test_search_discovers_links_and_reports_failures(monkeypatch):
    monkeypatch.setattr(advising_discovery, 'SEEDS', (BASE + 'directory', BASE + 'bad'))
    html = DIRECTORY.replace('</main>', '<a href="/de/456">Beratung FAQ</a></main>')
    responses = {BASE + 'directory': html, BASE + 'de/123': FAQ, BASE + 'de/456': FAQ}
    def fetch(url):
        if url not in responses:
            raise OSError('unavailable')
        return responses[url], url
    service = AdvisingDiscovery(fetcher=fetch)
    result = service.search('Anerkennung', limit=1)
    assert len(result.pages) == 3
    assert len(result.results) == 1
    assert 'Anerkennung' in result.results[0].text
    assert result.results_truncated
    assert result.seed_links_discovered == result.seed_links_attempted == 2
    assert result.errors[0].url == BASE + 'bad'
    assert result.pages[1].discovered_from == BASE + 'directory'
    discovered = service.discover()
    assert discovered.results == ()
    assert discovered.refreshed_at == result.refreshed_at


def test_search_rejects_empty_and_symbol_only_queries():
    service = AdvisingDiscovery(fetcher=lambda url: (DIRECTORY, url))
    for query in ('', '!', '???'):
        with pytest.raises(AlmaParseError):
            service.search(query)


def test_search_http_and_sdk_surfaces(monkeypatch):
    from fastapi.testclient import TestClient
    from tue_api_wrapper import api_routes_advising
    from tue_api_wrapper.api_server import app
    from tue_api_wrapper.sdk.public import PublicDirectoryApi

    monkeypatch.setattr(advising_discovery, 'SEEDS', (BASE + 'faq',))
    service = AdvisingDiscovery(fetcher=lambda url: (FAQ, url))
    monkeypatch.setattr(api_routes_advising, 'discovery', service)
    sdk = PublicDirectoryApi(advising_discovery=service)
    assert sdk.search_advising('Anerkennung').results[0].kind == 'list_item'
    client = TestClient(app)
    response = client.get('/api/people/advising/search', params={'query': 'Anerkennung'})
    assert response.status_code == 200
    assert response.json()['results'][0]['text'] == 'Anerkennung von Studienleistungen'
    assert client.get('/api/people/advising/search', params={'query': '???'}).status_code == 400
    assert client.get('/api/people/advising/discover').json()['pages'][0]['url'] == BASE + 'faq'
    refresh = client.post('/api/people/advising/refresh')
    assert refresh.status_code == 200
    assert refresh.json()['pages_attempted'] == 1


def test_directory_groups_degree_with_its_contact():
    html = '''<title>Studienfachberatung</title><main><h2>Computer Science</h2>
    <p class="ut-teaser">Studienfachberatung (Master)</p><p>Paul Stahl <a href="mailto:paul@uni-tuebingen.de">Mail</a></p>
    <p class="ut-teaser">Studienfachberatung (Lehramt)</p><p>Maria Knobelsdorf</p></main>'''
    _, passages, _ = parse_discovery_page(html, BASE, None)
    assert len(passages) == 2
    assert passages[0].kind == 'directory_contact'
    assert 'Master' in passages[0].text and 'Paul Stahl' in passages[0].text
    assert 'Knobelsdorf' not in passages[0].text
    assert passages[0].links[0].url == 'mailto:paul@uni-tuebingen.de'

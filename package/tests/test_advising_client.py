from __future__ import annotations

import pytest
import requests

from tue_api_wrapper.advising_client import AdvisingClient, parse_advising_page
from tue_api_wrapper.config import AlmaParseError

URL = 'https://uni-tuebingen.de/advising/'
HTML = '''<html><title>Paul Stahl | Universität Tübingen</title><main>
<div class="ut-box__block"><header><h2>Studienfachberatung</h2></header>
<div class="ut-box__text"><p>Paul Stahl</p><table>
<tr><td>E-Mail</td><td>studienfachberatung@cs.uni-tuebingen.de</td></tr>
<tr><td>Bürozeiten</td><td><p>Dienstags 14-17</p><p>Donnerstags 15-17</p></td></tr>
</table></div></div>
<div class="ut-box__block"><header><h2>Ich kann helfen bei</h2></header>
<table><thead><tr><th>Thema</th><th>Bitte gehen Sie wie folgt vor</th></tr></thead><tbody>
<tr><td>Anerkennung von Kursen</td><td>Modulbeschreibung beilegen</td></tr></tbody></table></div>
<div class="ut-box__block"><header><h2>Ich kann nicht helfen bei</h2></header>
<table><tr><th>Thema</th><th>Bitte kontaktieren Sie stattdessen</th></tr><tr><td>Kursanmeldung</td>
<td><a href="#" data-mailto-token="ocknvq,uvwfkgpdgtcvwpiBeu0wpk/vwgdkpigp0fg" data-mailto-vector="2">Studentische Studienberatung</a></td></tr>
<tr><td>Noten</td><td><a href="/pruefungssekretariat/">Prüfungssekretariat</a></td></tr></table></div>
</main></html>'''


def test_parses_guidance_contacts_and_alternative_links():
    page = parse_advising_page(HTML, source_url=URL)
    assert page.name == 'Paul Stahl'
    assert page.contact[1].value == 'Dienstags 14-17 Donnerstags 15-17'
    assert page.can_help[0].topic == 'Anerkennung von Kursen'
    assert page.can_help[0].guidance == 'Modulbeschreibung beilegen'
    assert page.cannot_help[0].links[0].url == 'mailto:studienberatung@cs.uni-tuebingen.de'
    assert page.cannot_help[1].links[0].url == 'https://uni-tuebingen.de/pruefungssekretariat/'


def test_unsupported_or_incomplete_page_fails_clearly():
    with pytest.raises(AlmaParseError, match='No supported'):
        parse_advising_page('<main><h2>Other page</h2></main>', source_url=URL)
    with pytest.raises(AlmaParseError, match='missing or empty'):
        parse_advising_page('<main><div class="ut-box__block"><h2>Ich kann helfen bei</h2></div></main>', source_url=URL)


@pytest.mark.parametrize('url', ['http://uni-tuebingen.de/', 'https://uni-tuebingen.de.evil.test/',
                                'https://localhost/', 'https://uni-tuebingen.de:8443/'])
def test_rejects_untrusted_urls_before_request(url):
    class Session:
        def get(self, *_args, **_kwargs):
            pytest.fail('Must not request an untrusted URL')
    with pytest.raises(AlmaParseError, match='HTTPS on uni-tuebingen.de'):
        AdvisingClient(session=Session()).fetch(url)


def test_rejects_untrusted_redirect():
    class Session:
        def get(self, *_args, **_kwargs):
            response = requests.Response()
            response.status_code = 302
            response.headers['Location'] = 'http://127.0.0.1/'
            return response
    with pytest.raises(AlmaParseError, match='HTTPS on uni-tuebingen.de'):
        AdvisingClient(session=Session()).fetch(URL)


def test_http_endpoint_serializes_guidance_and_reports_bad_url(monkeypatch):
    from fastapi.testclient import TestClient
    from tue_api_wrapper import api_routes_products
    from tue_api_wrapper.api_server import app

    page = parse_advising_page(HTML, source_url=URL)
    monkeypatch.setattr(api_routes_products.advising_client, 'fetch', lambda url: page)
    response = TestClient(app).get('/api/people/advising', params={'url': URL})
    assert response.status_code == 200
    assert response.json()['cannot_help'][0]['links'][0]['url'] == 'mailto:studienberatung@cs.uni-tuebingen.de'

    def reject(_url):
        raise AlmaParseError('Invalid advising URL')

    monkeypatch.setattr(api_routes_products.advising_client, 'fetch', reject)
    response = TestClient(app).get('/api/people/advising', params={'url': 'http://localhost/'})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Invalid advising URL'


def test_legacy_page_responsibility_tables():
    html = '''<title>Old | University</title><main>
      <div class="ut-grid__col-2"><div class="ut-box__text"><p><strong>Louisa Flüchter</strong><br>
      <a href="mailto:old@uni-tuebingen.de">old@uni-tuebingen.de</a></p></div></div>
      <p><strong>Ich kann helfen bei</strong></p><table><tr><td>Anerkennung</td><td>Beschreibung beilegen</td></tr></table>
      <p>Ich kann Ihnen <strong>nicht</strong> helfen bei</p><table><tr><td>Kursanmeldung</td><td>Andere Beratung</td></tr></table>
      </main>'''
    page = parse_advising_page(html, source_url='https://db.cs.uni-tuebingen.de/studienfachberatung/')
    assert page.name == 'Louisa Flüchter'
    assert page.contact[0].links[0].url == 'mailto:old@uni-tuebingen.de'
    assert page.can_help[0].topic == 'Anerkennung'
    assert page.cannot_help[0].topic == 'Kursanmeldung'

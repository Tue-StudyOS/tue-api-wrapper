from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from tue_api_wrapper import api_routes_products, mcp_campus, study_radar_cli
from tue_api_wrapper.advising_client import AdvisingClient
from tue_api_wrapper.api_server import app
from tue_api_wrapper.sdk.public import PublicDirectoryApi

URL = 'https://uni-tuebingen.de/advising/'


def test_client_and_sdk_require_and_forward_url(monkeypatch):
    client = AdvisingClient()
    with pytest.raises(TypeError):
        client.fetch()
    monkeypatch.setattr(client, 'fetch_html', lambda url: (
        b'<title>Advising</title><main><div class="ut-box__block"><h2>Ich kann helfen bei</h2>'
        b'<table><tr><td>Topic</td><td>Guidance</td></tr></table></div></main>', url))
    assert client.fetch(URL).source_url == URL
    sdk = PublicDirectoryApi(advising_client=client)
    with pytest.raises(TypeError):
        sdk.advising_page()
    assert sdk.advising_page(URL).source_url == URL


def test_http_requires_url_and_passes_it_to_reader(monkeypatch):
    seen = []
    monkeypatch.setattr(api_routes_products.advising_client, 'fetch', lambda url: seen.append(url) or {'source_url': url})
    client = TestClient(app)
    assert client.get('/api/people/advising').status_code == 422
    assert client.get('/api/people/advising', params={'url': ''}).status_code == 422
    assert seen == []
    result = client.get('/api/people/advising', params={'url': URL})
    assert result.status_code == 200
    assert result.json()['source_url'] == URL
    assert seen == [URL]


def test_cli_requires_target_and_passes_it_to_reader(monkeypatch, capsys):
    for args in (['advising'], ['advising', '--target', '   ']):
        with pytest.raises(SystemExit) as error:
            study_radar_cli.main(args)
        assert error.value.code == 2
        assert 'advising requires --target' in capsys.readouterr().err
    client = SimpleNamespace(directory=SimpleNamespace(advising_page=lambda url: {'source_url': url}))
    monkeypatch.setattr(study_radar_cli, 'TuebingenPublicClient', lambda: client)
    assert study_radar_cli.main(['advising', '--target', URL]) == 0
    assert json.loads(capsys.readouterr().out)['source_url'] == URL


def test_mcp_requires_url_and_passes_it_to_reader(monkeypatch):
    tools = {}
    class Server:
        def tool(self):
            return lambda function: tools.setdefault(function.__name__, function)
    client = SimpleNamespace(directory=SimpleNamespace(advising_page=lambda url: {'source_url': url}))
    monkeypatch.setattr(mcp_campus, 'TuebingenPublicClient', lambda: client)
    mcp_campus.register_campus_tools(Server())
    with pytest.raises(TypeError):
        tools['campus_advising_page']()
    assert tools['campus_advising_page'](URL)['source_url'] == URL

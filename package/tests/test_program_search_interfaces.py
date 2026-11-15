import json
from types import SimpleNamespace
import pytest

from tue_api_wrapper import study_radar_cli
from tue_api_wrapper.mcp_server import _register_public_tools


def test_program_search_cli_passes_degree_and_subject_filters(monkeypatch, capsys):
    calls = []
    alma = SimpleNamespace(search_modules=lambda **kwargs: calls.append(kwargs) or {'results': [], 'truncated': False})
    monkeypatch.setattr(study_radar_cli, 'TuebingenPublicClient', lambda: SimpleNamespace(alma=alma))
    assert study_radar_cli.main(['alma-program-search', '--degree', '89', '--subject', '2385',
                                 '--element-type', '5', '--limit', '5']) == 0
    assert calls[0]['degrees'] == ('89',) and calls[0]['subjects'] == ('2385',)
    assert calls[0]['element_types'] == ('5',)
    assert json.loads(capsys.readouterr().out)['truncated'] is False


def test_program_filters_and_search_are_available_to_mcp():
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    calls = []
    alma = SimpleNamespace(module_search_filters=lambda: {'degrees': ['Master']},
                           search_modules=lambda **kwargs: calls.append(kwargs) or {'results': []})
    _register_public_tools(Server(), SimpleNamespace(alma=alma))
    assert tools['public_alma_program_filters']()['degrees'] == ['Master']
    tools['public_alma_search_program'](degrees=['89'], subjects=['2385'])
    assert calls[0]['degrees'] == ('89',) and calls[0]['subjects'] == ('2385',)


def test_public_sdk_forwards_programme_filters():
    from tue_api_wrapper.sdk.public import PublicAlmaApi
    calls = []
    client = SimpleNamespace(search_public_module_descriptions=lambda **kwargs: calls.append(kwargs) or {'results': []})
    PublicAlmaApi(client=client).search_modules(degrees=('89',), subjects=('2385',), element_types=('5',))
    assert calls[0]['degrees'] == ('89',)
    assert calls[0]['subjects'] == ('2385',)
    assert calls[0]['element_types'] == ('5',)


def test_missing_alma_filter_field_fails_instead_of_silently_broadening(monkeypatch):
    from tue_api_wrapper.client import AlmaClient
    from tue_api_wrapper.config import AlmaParseError
    client = AlmaClient()
    contract = SimpleNamespace(fields=SimpleNamespace(degree=None))
    monkeypatch.setattr(client, '_fetch_advanced_public_module_search_contract', lambda: contract)
    with pytest.raises(AlmaParseError, match='degree'):
        client._search_public_module_descriptions_once(query='', title='', number='', element_type='',
                                                      language='', degree='89', subject='', faculty='', max_results=5)


def test_unknown_alma_filter_value_fails_before_request(monkeypatch):
    from tue_api_wrapper.client import AlmaClient
    from tue_api_wrapper.config import AlmaParseError
    client = AlmaClient()
    contract = SimpleNamespace(fields=SimpleNamespace(degree='degree_input'),
                               filters=SimpleNamespace(degrees=(SimpleNamespace(value='89'),)))
    monkeypatch.setattr(client, '_fetch_advanced_public_module_search_contract', lambda: contract)
    with pytest.raises(AlmaParseError, match='degree'):
        client._search_public_module_descriptions_once(query='', title='', number='', element_type='',
                                                      language='', degree='invalid', subject='', faculty='', max_results=5)

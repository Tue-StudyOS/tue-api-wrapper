from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_search_raw import fetch_raw_ilias_search
from tue_api_wrapper import study_radar_cli


BASE = "https://ovidius.uni-tuebingen.de"
FORM = '''<form action="/ilias.php?baseClass=ilsearchcontrollergui&amp;cmd=post&amp;fallbackCmd=performSearch&amp;rtoken=local" method="post">
<input name="term" type="text" /><input type="hidden" name="area" value="0" />
<input type="submit" name="cmd[performSearch]" value="Suche" /></form>'''


def response(text, status=200, url=BASE + "/ilias.php?baseClass=ilSearchControllerGUI"):
    return SimpleNamespace(text=text, status_code=status, url=url, headers={})


def test_form_only_returns_raw_even_when_form_parser_would_fail():
    session = Mock()
    session.get.return_value = response("<form>new markup</form>")
    result = fetch_raw_ilias_search(SimpleNamespace(session=session, timeout_seconds=10), form_only=True)
    assert result["body"] == "<form>new markup</form>"
    session.post.assert_not_called()


def test_search_returns_raw_results_without_results_parser():
    session = Mock()
    session.get.return_value = response(FORM)
    session.post.return_value = response("<section>new result format</section>")
    result = fetch_raw_ilias_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    assert result["body"] == "<section>new result format</section>"
    assert session.post.call_args.kwargs["data"]["term"] == "Algorithms"
    assert session.post.call_args.kwargs["allow_redirects"] is False


def test_refuses_external_form_action_without_posting():
    session = Mock()
    session.get.return_value = response(FORM.replace('action="/ilias.php', 'action="https://evil.example/ilias.php'))
    with pytest.raises(AlmaParseError):
        fetch_raw_ilias_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    session.post.assert_not_called()


def test_refuses_non_search_command_on_ilias_host():
    session = Mock()
    session.get.return_value = response(FORM.replace("cmd=post", "cmd=delete"))
    with pytest.raises(AlmaParseError):
        fetch_raw_ilias_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    session.post.assert_not_called()


def test_redirected_initial_response_is_returned_without_posting():
    session = Mock()
    session.get.return_value = response("redirect", status=302)
    result = fetch_raw_ilias_search(SimpleNamespace(session=session, timeout_seconds=10), query="Algorithms")
    assert result["stage"] == "form"
    assert result["status_code"] == 302
    session.post.assert_not_called()


def test_cli_returns_raw_ilias_json_and_nonzero_on_redirect(monkeypatch, capsys):
    client = SimpleNamespace(ilias=SimpleNamespace(client=object()), close=lambda: None)
    monkeypatch.setattr(study_radar_cli, "make_client", lambda _: (client, "user"))
    monkeypatch.setattr(study_radar_cli, "fetch_raw_ilias_search", lambda *args, **kwargs: {"status_code": 302, "stage": "form", "body": "redirect"})
    assert study_radar_cli.main(["raw-ilias-search", "--query", "Algorithms"]) == 1
    import json
    assert json.loads(capsys.readouterr().out)["stage"] == "form"


def test_cli_requires_query_or_form_only():
    with pytest.raises(SystemExit) as error:
        study_radar_cli.main(["raw-ilias-search"])
    assert error.value.code == 2

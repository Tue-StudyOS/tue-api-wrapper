import json
from types import SimpleNamespace

import pytest

from tue_api_wrapper import registration_cli, registration_workflows


def preview():
    return {"kind": "course", "target": "https://alma.example/alma/x", "account": "student",
            "title": "Math", "number": "M1", "action": "ANMELDUNG",
            "option": {"planelement_id": "1", "label": "Path", "action_name": "register"}, "messages": []}


def test_execute_without_terminal_never_submits(monkeypatch, capsys):
    monkeypatch.setattr(registration_cli, "make_client", lambda _: (SimpleNamespace(alma=SimpleNamespace(client=object()), close=lambda: None), "student"))
    monkeypatch.setattr(registration_cli, "prepare_selected", lambda *args, **kwargs: preview())
    monkeypatch.setattr(registration_cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(registration_cli, "execute_registration", lambda *args: pytest.fail("must not submit"))
    assert registration_cli.main(["execute", "course", "--url", "https://alma.example/alma/x", "--option", "1"]) == 1
    assert "terminal" in capsys.readouterr().err.lower()


def test_prepare_returns_only_selected_reviewable_option(monkeypatch):
    from tue_api_wrapper.alma_course_registration_models import AlmaCourseRegistrationOption
    option = AlmaCourseRegistrationOption(planelement_id="1", label="Path", action_name="register")
    options = SimpleNamespace(title="Math", number="M1", action="ANMELDUNG", options=(option,), messages=())
    monkeypatch.setattr(registration_workflows, "prepare_course_registration", lambda *args: options)
    result = registration_workflows.prepare_selected(object(), "student", "course", "https://alma.example/alma/x", None, "1")
    assert result["option"]["label"] == "Path"
    assert result["account"] == "student"


def test_write_exception_returns_unknown_and_never_retries(monkeypatch):
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("connection lost")
    monkeypatch.setattr(registration_workflows, "register_for_course", fail)
    result = registration_workflows.execute_registration(object(), preview())
    assert result["outcome"] == "unknown"
    assert len(calls) == 1


def test_cli_decline_does_not_submit(monkeypatch, capsys):
    client = SimpleNamespace(alma=SimpleNamespace(client=object()), close=lambda: None)
    monkeypatch.setattr(registration_cli, "make_client", lambda _: (client, "student"))
    monkeypatch.setattr(registration_cli, "prepare_selected", lambda *args: preview())
    monkeypatch.setattr(registration_cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "no")
    monkeypatch.setattr(registration_cli, "execute_registration", lambda *args: pytest.fail("must not submit"))
    assert registration_cli.main(["execute", "course", "--url", "https://alma.example/alma/x", "--option", "1"]) == 1
    assert "Cancelled" in capsys.readouterr().err


def test_cli_submits_only_after_confirmation_and_reports_unverified(monkeypatch, capsys):
    client = SimpleNamespace(alma=SimpleNamespace(client=object()), close=lambda: None)
    monkeypatch.setattr(registration_cli, "make_client", lambda _: (client, "student"))
    monkeypatch.setattr(registration_cli, "prepare_selected", lambda *args: preview())
    monkeypatch.setattr(registration_cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "REGISTER")
    monkeypatch.setattr(registration_cli, "execute_registration", lambda *args: {"outcome": "unverified"})
    assert registration_cli.main(["execute", "course", "--url", "https://alma.example/alma/x", "--option", "1"]) == 1
    assert '"unverified"' in capsys.readouterr().out


def test_mcp_registers_preview_tools_without_direct_execution():
    from tue_api_wrapper.mcp_registration import register_registration_tools
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    register_registration_tools(Server(), None)
    assert set(tools) == {"alma_registration_inspect", "alma_registration_prepare"}

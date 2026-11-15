import json
from types import SimpleNamespace

from tue_api_wrapper import study_radar_cli
from tue_api_wrapper.mcp_study import register_study_tools


def test_cli_prints_json_and_returns_nonzero_for_partial_failure(monkeypatch, capsys):
    client = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(study_radar_cli, "make_client", lambda _: (client, "student"))
    monkeypatch.setattr(study_radar_cli, "collect_study_radar", lambda *args, **kwargs: {
        "sources": {"ilias": {"status": "error", "error": "Timeout"}}
    })
    assert study_radar_cli.main([]) == 1
    assert json.loads(capsys.readouterr().out)["sources"]["ilias"]["status"] == "error"


def test_mcp_radar_tools_return_observations_and_changes(monkeypatch, tmp_path):
    from tue_api_wrapper import mcp_study
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    client = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(mcp_study, "make_client", lambda _: (client, "student"))
    monkeypatch.setattr(mcp_study, "state_path", lambda _: tmp_path / "radar.json")
    monkeypatch.setattr(mcp_study, "collect_study_radar", lambda *args, **kwargs: {
        "sources": {"ilias": {"status": "ok", "items": [{"id": "1", "title": "Sheet"}]}}
    })
    register_study_tools(Server(), None)
    assert tools["study_radar_read"]()["sources"]["ilias"]["items"][0]["title"] == "Sheet"
    assert tools["study_radar_changes"]()["sources"]["ilias"]["baseline"] is True


def test_cli_exams_returns_json_from_existing_sdk(monkeypatch, capsys):
    client = SimpleNamespace(alma=SimpleNamespace(exams=lambda: [{"title": "Algorithms", "grade": "1.0"}]), close=lambda: None)
    monkeypatch.setattr(study_radar_cli, "make_client", lambda _: (client, "student"))
    assert study_radar_cli.main(["exams"]) == 0
    assert json.loads(capsys.readouterr().out)["items"][0]["title"] == "Algorithms"


def test_cli_public_buildings_needs_no_credentials(monkeypatch, capsys):
    monkeypatch.setattr(study_radar_cli, "TuebingenPublicClient", lambda: SimpleNamespace(campus=SimpleNamespace(buildings=lambda: {"buildings": ["Kupferbau"]})))
    assert study_radar_cli.main(["buildings"]) == 0
    assert json.loads(capsys.readouterr().out)["buildings"] == ["Kupferbau"]


def test_mcp_exposes_notices_and_mail_detail(monkeypatch):
    from tue_api_wrapper import mcp_study
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    client = SimpleNamespace(
        alma=SimpleNamespace(portal_messages=lambda: {"items": [{"title": "Notice"}]}),
        mail=SimpleNamespace(message=lambda uid, mailbox: {"uid": uid, "mailbox": mailbox}),
        close=lambda: None,
    )
    monkeypatch.setattr(mcp_study, "make_client", lambda _: (client, "student"))
    register_study_tools(Server(), None)
    assert tools["study_alma_notices"]()["items"][0]["title"] == "Notice"
    assert tools["study_mail_message"]("123", "INBOX")["uid"] == "123"


def test_mcp_timetable_returns_bounded_occurrences(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from tue_api_wrapper import mcp_study
    from tue_api_wrapper.models import CalendarOccurrence
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    occurrence = CalendarOccurrence("Seminar", datetime.now(timezone.utc) + timedelta(days=1), None, "Room A", None, uid="1")
    client = SimpleNamespace(alma=SimpleNamespace(timetable=lambda term: SimpleNamespace(term_label=term, occurrences=[occurrence])), close=lambda: None)
    monkeypatch.setattr(mcp_study, "make_client", lambda _: (client, "student"))
    register_study_tools(Server(), None)
    result = tools["study_timetable"](days=7, term="Winter 2026/27")
    assert result["items"][0]["location"] == "Room A"
    assert "export_url" not in result

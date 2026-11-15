from types import SimpleNamespace

from tue_api_wrapper.study_radar import collect_study_radar
from tue_api_wrapper.study_radar_state import compare_and_save


def test_collection_keeps_other_sources_when_one_fails():
    def unavailable(**kwargs):
        raise RuntimeError("unreachable")

    assignment = SimpleNamespace(title="Sheet 1", url="https://ilias/a", due_at="2026-11-20", due_hint=None, status="open")
    client = SimpleNamespace(
        ilias=SimpleNamespace(assignment_deadlines=lambda **kwargs: [SimpleNamespace(course_title="Math", course_url="https://ilias/course", exercise_url="https://ilias/exercise", assignment=assignment)], quiz_deadlines=unavailable),
        moodle=SimpleNamespace(deadlines=lambda **kwargs: SimpleNamespace(items=[], source_url="https://moodle/")),
        alma=SimpleNamespace(portal_messages=lambda: SimpleNamespace(items=[])),
    )
    result = collect_study_radar(client)
    assert result["sources"]["ilias_quizzes"]["status"] == "error"
    assert result["sources"]["ilias_assignments"]["items"][0]["title"] == "Sheet 1"
    assert result["sources"]["moodle_deadlines"]["status"] == "ok"


def test_change_tracking_preserves_failed_source_and_reports_changes(tmp_path):
    def observation(status, items):
        return {"sources": {"assignments": {"status": status, "items": items}}}

    item = {"id": "a", "title": "Sheet 1", "due": "2026-11-20"}
    first = compare_and_save(observation("ok", [item]), tmp_path / "state.json")
    assert first["sources"]["assignments"]["baseline"] is True
    failed = compare_and_save(observation("error", []), tmp_path / "state.json")
    assert failed["sources"]["assignments"]["status"] == "error"
    changed = compare_and_save(observation("ok", [{**item, "due": "2026-11-21"}]), tmp_path / "state.json")
    assert changed["sources"]["assignments"]["changed"][0]["before"]["due"] == "2026-11-20"
    assert changed["sources"]["assignments"]["changed"][0]["after"]["due"] == "2026-11-21"


def test_missing_items_are_not_reported_as_removed(tmp_path):
    path = tmp_path / "state.json"
    compare_and_save({"sources": {"x": {"status": "ok", "items": [{"id": "1", "title": "A"}]}}}, path)
    result = compare_and_save({"sources": {"x": {"status": "ok", "items": []}}}, path)
    assert result["sources"]["x"]["added"] == []
    assert result["sources"]["x"]["changed"] == []


def test_assignment_identity_survives_title_and_session_url_changes():
    assignment = SimpleNamespace(title="First title", url="https://ilias/item?ass_id=42&session=one", due_at=None, due_hint=None, status=None)
    row = SimpleNamespace(course_title="Math", course_url="https://ilias/course", exercise_url="https://ilias/exercise", assignment=assignment)
    client = SimpleNamespace(ilias=SimpleNamespace(assignment_deadlines=lambda **kwargs: [row], quiz_deadlines=lambda **kwargs: []),
                             moodle=SimpleNamespace(deadlines=lambda **kwargs: SimpleNamespace(items=[])),
                             alma=SimpleNamespace(portal_messages=lambda: SimpleNamespace(items=[])))
    first = collect_study_radar(client)["sources"]["ilias_assignments"]["items"][0]["id"]
    assignment.title = "New title"
    assignment.url = "https://ilias/item?ass_id=42&session=two"
    second = collect_study_radar(client)["sources"]["ilias_assignments"]["items"][0]["id"]
    assert first == second

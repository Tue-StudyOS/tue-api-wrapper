from datetime import datetime, timezone
from types import SimpleNamespace

from tue_api_wrapper.ics import expand_ics_events
from tue_api_wrapper.models import CalendarEvent, CalendarOccurrence
from tue_api_wrapper.study_radar_state import compare_and_save
from tue_api_wrapper.study_timetable import collect_timetable


def test_calendar_expansion_retains_source_identifier():
    event = CalendarEvent("Lecture", datetime(2026, 11, 20, 9, tzinfo=timezone.utc), None, None, None, "course-1", None, ())
    assert expand_ics_events((event,), "Winter 2026/27")[0].uid == "course-1"


def test_timetable_room_and_time_change_is_detected(tmp_path):
    first = CalendarOccurrence("Lecture", datetime(2026, 11, 20, 9, tzinfo=timezone.utc), None, "A", None, uid="course-1")
    second = CalendarOccurrence("Lecture", datetime(2026, 11, 20, 10, tzinfo=timezone.utc), None, "B", None, uid="course-1")
    alma = SimpleNamespace(timetable=lambda term: SimpleNamespace(term_label=term, occurrences=[first]))
    now = datetime(2026, 11, 19, tzinfo=timezone.utc)
    data = collect_timetable(alma, term="Winter 2026/27", days=7, limit=10, now=now)
    path = tmp_path / "state.json"
    compare_and_save({"sources": {"alma_timetable": data}}, path)
    alma.timetable = lambda term: SimpleNamespace(term_label=term, occurrences=[second])
    data = collect_timetable(alma, term="Winter 2026/27", days=7, limit=10, now=now)
    changes = compare_and_save({"sources": {"alma_timetable": data}}, path)["sources"]["alma_timetable"]
    assert changes["changed"][0]["after"]["location"] == "B"
    assert changes["added"] == []


def test_timetable_does_not_match_distinct_occurrences_with_same_uid_and_day():
    one = CalendarOccurrence("Lecture", datetime(2026, 11, 20, 9, tzinfo=timezone.utc), None, "A", None, uid="course-1")
    two = CalendarOccurrence("Lecture", datetime(2026, 11, 20, 13, tzinfo=timezone.utc), None, "A", None, uid="course-1")
    alma = SimpleNamespace(timetable=lambda term: SimpleNamespace(term_label=term, occurrences=[one, two]))
    data = collect_timetable(alma, term="Winter 2026/27", days=7, limit=10, now=datetime(2026, 11, 19, tzinfo=timezone.utc))
    assert len({item["id"] for item in data["items"]}) == 2
    assert data["identity_warning"] is True


def test_timetable_changes_report_truncation_and_identity_limits(tmp_path):
    observation = {"scope": {"lookahead_days": 7}, "sources": {"alma_timetable": {
        "status": "ok", "items": [], "truncated": True, "identity_warning": True,
        "term": "Winter 2026/27", "window_start": "2026-11-19", "window_end": "2026-11-26"}}}
    changes = compare_and_save(observation, tmp_path / "state.json")
    assert changes["sources"]["alma_timetable"]["truncated"] is True
    assert changes["sources"]["alma_timetable"]["identity_warning"] is True
    assert changes["scope"]["lookahead_days"] == 7

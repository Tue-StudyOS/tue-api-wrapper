from dataclasses import replace

from tue_api_wrapper.exam_summary import summarize_exam_records
from tue_api_wrapper.models import AlmaExamNode


def _exam(**overrides):
    base = AlmaExamNode(
        level=0, kind="exam", title="Test", number="1", attempt=None,
        grade="1,7", cp="6", malus=None, status="BE", free_trial=None,
        remark=None, exception=None, release_date=None,
    )
    return replace(base, **overrides)


def test_parent_credit_totals_are_not_counted_twice():
    rows = [_exam(cp="12"), _exam(level=1), _exam(level=1)]
    assert summarize_exam_records(rows) == (2, 12.0)


def test_explicit_failed_status_overrides_grade():
    assert summarize_exam_records([_exam(status="NB", grade="1,0")])[0] == 0


def test_missing_status_accepts_only_passing_numeric_grades():
    rows = [_exam(status=None, grade=value, cp=None) for value in ["1,7", "4.0", "5,0", "5.0", "pending", "-"]]
    assert summarize_exam_records(rows) == (2, 0.0)


def test_invalid_credit_values_do_not_break_dashboard():
    rows = [_exam(cp=value) for value in ["-", "pending", "nan", "inf", "-1", "3,5"]]
    assert summarize_exam_records(rows) == (6, 3.5)


def test_dashboard_totals_include_records_beyond_display_limit():
    from test_dashboard_builder import _FakeAlmaClient, _FakeIliasClient
    from tue_api_wrapper.dashboard_builder import build_dashboard_payload

    class Alma(_FakeAlmaClient):
        def fetch_exam_overview(self):
            return [_exam(title=f"Exam {index}") for index in range(10)]

    dashboard = build_dashboard_payload(
        limit=1, include_course_assignments=False,
        load_alma_client=Alma, load_ilias_client=_FakeIliasClient,
        load_mail_panel=lambda **_: {"available": False, "items": []},
        load_talks_panel=lambda **_: {"available": False, "totalHits": 0, "items": [], "error": None},
    )
    assert len(dashboard["exams"]) == 1
    assert dashboard["study"]["passedExamCount"] == 10
    assert dashboard["study"]["trackedCredits"] == 60.0

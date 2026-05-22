from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_course_assignments_models import AlmaTimetableCourseAssignmentsPage
from tue_api_wrapper.alma_portal_messages_models import AlmaPortalMessagesPage
from tue_api_wrapper.alma_planner_models import AlmaStudyPlannerPage, AlmaStudyPlannerViewState
from tue_api_wrapper.alma_studyservice_models import AlmaStudyServicePage
from tue_api_wrapper.dashboard_builder import build_dashboard_payload
from tue_api_wrapper.models import (
    AlmaDocumentReport,
    AlmaEnrollmentPage,
    AlmaExamNode,
    CalendarOccurrence,
    IliasLink,
    IliasMembershipItem,
    IliasRootPage,
    IliasTaskItem,
    TimetableResult,
)


class _FakeAlmaClient:
    studyservice_url = "https://alma.example/studyservice"

    def __init__(self, occurrences: tuple[CalendarOccurrence, ...] | None = None) -> None:
        self._occurrences = occurrences

    def fetch_timetable_for_term(self, term_label: str) -> TimetableResult:
        return TimetableResult(
            term_label=term_label,
            term_id="229",
            export_url="https://alma.example/export.ics",
            raw_ics="",
            events=(),
            occurrences=self._occurrences
            or (
                _occurrence("ML Seminar", datetime(2026, 4, 13, 10, 15), datetime(2026, 4, 13, 11, 45)),
            ),
            available_terms={term_label: "229"},
        )

    def fetch_enrollment_page(self) -> AlmaEnrollmentPage:
        return AlmaEnrollmentPage(
            selected_term="Sommer 2026",
            available_terms={"Sommer 2026": "229"},
            message=None,
        )

    def fetch_exam_overview(self) -> list[AlmaExamNode]:
        return [
            AlmaExamNode(
                level=0,
                kind="exam",
                title="Machine Learning",
                number="ML-1",
                attempt=None,
                grade="1,7",
                cp="6",
                malus=None,
                status="BE",
                free_trial=None,
                remark=None,
                exception=None,
                release_date=None,
            )
        ]

    def fetch_studyservice_contract(self) -> AlmaStudyServicePage:
        return AlmaStudyServicePage(
            action_url="https://alma.example/studyservice",
            payload={},
            reports=(AlmaDocumentReport(label="Transcript", trigger_name="report:transcript"),),
            latest_download_url="https://alma.example/current.pdf",
            banner_text=None,
            person_name=None,
            active_tab_label=None,
            tabs=(),
            output_requests=(),
            contact_sections=(),
        )

    def fetch_study_planner(self) -> AlmaStudyPlannerPage:
        return AlmaStudyPlannerPage(
            title="Studienplaner",
            page_url="https://alma.example/planner",
            semesters=(),
            modules=(),
            view_state=AlmaStudyPlannerViewState(True, True, False),
        )

    def fetch_portal_messages(self) -> AlmaPortalMessagesPage:
        return AlmaPortalMessagesPage(page_url="https://alma.example/start", items=())


class _FakeIliasClient:
    def fetch_root_page(self) -> IliasRootPage:
        return IliasRootPage(
            title="ILIAS",
            mainbar_links=(IliasLink(label="Dashboard", url="https://ovidius.example/dashboard"),),
            top_categories=(),
        )

    def fetch_membership_overview(self) -> tuple[IliasMembershipItem, ...]:
        return (
            IliasMembershipItem(
                title="ML Group",
                url="https://ovidius.example/group",
                kind="grp",
                description=None,
                info_url=None,
                properties=(),
            ),
        )

    def fetch_task_overview(self) -> tuple[IliasTaskItem, ...]:
        return (
            IliasTaskItem(
                title="Assignment 1",
                url="https://ovidius.example/task",
                item_type="Exercise",
                start=None,
                end="24. Apr 2026",
            ),
        )


class DashboardBuilderTests(unittest.TestCase):
    def test_study_systems_are_loaded_concurrently(self) -> None:
        alma_started = Event()
        ilias_started = Event()

        def load_alma_client() -> _FakeAlmaClient:
            alma_started.set()
            self.assertTrue(ilias_started.wait(1), "ILIAS did not start while Alma was blocked.")
            return _FakeAlmaClient()

        def load_ilias_client() -> _FakeIliasClient:
            ilias_started.set()
            self.assertTrue(alma_started.wait(1), "Alma did not start while ILIAS was blocked.")
            return _FakeIliasClient()

        assignments = AlmaTimetableCourseAssignmentsPage(
            term_label="Sommer 2026",
            term_id="229",
            total_credits=6.0,
            resolved_credit_count=1,
            unresolved_credit_count=0,
            unresolved_credit_summaries=(),
            courses=(),
        )
        with patch("tue_api_wrapper.dashboard_builder.build_timetable_course_assignments", return_value=assignments):
            dashboard = build_dashboard_payload(
                term_label="Sommer 2026",
                load_alma_client=load_alma_client,
                load_ilias_client=load_ilias_client,
                load_mail_panel=lambda *, limit: {"available": True, "items": []},
                load_talks_panel=lambda *, limit: {"available": False, "totalHits": 0, "items": [], "error": None},
            )

        self.assertEqual(dashboard["termLabel"], "Sommer 2026")
        self.assertEqual(dashboard["documents"]["sourcePageUrl"], _FakeAlmaClient.studyservice_url)
        self.assertEqual(dashboard["study"]["currentSemesterCredits"], 6.0)
        self.assertEqual(dashboard["ilias"]["tasks"][0]["title"], "Assignment 1")

    def test_course_assignments_can_be_deferred(self) -> None:
        with patch("tue_api_wrapper.dashboard_builder.build_timetable_course_assignments") as assignments:
            dashboard = build_dashboard_payload(
                term_label="Sommer 2026",
                include_course_assignments=False,
                load_alma_client=lambda: _FakeAlmaClient(),
                load_ilias_client=lambda: _FakeIliasClient(),
                load_mail_panel=lambda *, limit: {"available": True, "items": []},
                load_talks_panel=lambda *, limit: {"available": False, "totalHits": 0, "items": [], "error": None},
            )

        assignments.assert_not_called()
        self.assertIsNone(dashboard["study"]["currentSemesterCredits"])
        self.assertNotIn("Saved semester CP", [metric["label"] for metric in dashboard["metrics"]])

    def test_dashboard_agenda_uses_upcoming_occurrences(self) -> None:
        alma = _FakeAlmaClient(
            (
                _occurrence("Past lecture", datetime(2026, 4, 19, 10, 0), datetime(2026, 4, 19, 12, 0)),
                _occurrence("Today lecture", datetime(2026, 5, 3, 10, 0), datetime(2026, 5, 3, 12, 0)),
                _occurrence("Future lecture", datetime(2026, 5, 11, 10, 0), datetime(2026, 5, 11, 12, 0)),
            )
        )

        dashboard = build_dashboard_payload(
            term_label="Sommer 2026",
            limit=1,
            include_course_assignments=False,
            today=date(2026, 5, 3),
            load_alma_client=lambda: alma,
            load_ilias_client=lambda: _FakeIliasClient(),
            load_mail_panel=lambda *, limit: {"available": True, "items": []},
            load_talks_panel=lambda *, limit: {"available": False, "totalHits": 0, "items": [], "error": None},
        )

        self.assertEqual([item["summary"] for item in dashboard["agenda"]["items"]], ["Today lecture", "Future lecture"])
        self.assertEqual(_metric_value(dashboard, "Upcoming events"), 2)


def _occurrence(
    summary: str,
    start: datetime,
    end: datetime,
) -> CalendarOccurrence:
    return CalendarOccurrence(
        summary=summary,
        start=start,
        end=end,
        location="Sand 14",
        description=None,
    )


def _metric_value(dashboard: dict[str, object], label: str) -> object:
    metrics = dashboard["metrics"]
    assert isinstance(metrics, list)
    for metric in metrics:
        if isinstance(metric, dict) and metric.get("label") == label:
            return metric.get("value")
    raise AssertionError(f"Metric {label!r} not found.")


if __name__ == "__main__":
    unittest.main()

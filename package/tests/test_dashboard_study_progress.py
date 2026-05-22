from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_course_assignments_models import AlmaTimetableCourseAssignmentsPage
from tue_api_wrapper.alma_enrollment_models import AlmaEnrollmentEntry
from tue_api_wrapper.alma_portal_messages_models import AlmaPortalMessagesPage
from tue_api_wrapper.alma_planner_models import (
    AlmaStudyPlannerModule,
    AlmaStudyPlannerPage,
    AlmaStudyPlannerViewState,
)
from tue_api_wrapper.alma_studyservice_models import AlmaStudyServicePage
from tue_api_wrapper.dashboard_builder import build_dashboard_payload
from tue_api_wrapper.models import AlmaEnrollmentPage, TimetableResult


class _FakeAlma:
    studyservice_url = "https://alma.example/studyservice"

    def fetch_timetable_for_term(self, term_label: str) -> TimetableResult:
        return TimetableResult(term_label, "229", "", "", (), (), {term_label: "229"})

    def fetch_enrollment_page(self) -> AlmaEnrollmentPage:
        return AlmaEnrollmentPage(
            selected_term="Sommer 2026",
            available_terms={"Sommer 2026": "229"},
            message=None,
            entries=(
                AlmaEnrollmentEntry(
                    title="Neural Data Science",
                    number="GTCNEURO",
                    event_type="Vorlesung/Übung",
                    status="storniert",
                    semester="SoSe 2026",
                    schedule_text="jeden Mittwoch von 10:15 bis 11:45",
                    detail_url="https://alma.example/detail",
                ),
            ),
        )

    def fetch_exam_overview(self):
        return []

    def fetch_studyservice_contract(self) -> AlmaStudyServicePage:
        return AlmaStudyServicePage(
            action_url="https://alma.example/studyservice",
            payload={},
            reports=(),
            latest_download_url=None,
            banner_text=None,
            person_name=None,
            active_tab_label=None,
            tabs=(),
            output_requests=(),
            contact_sections=(),
        )

    def fetch_study_planner(self) -> AlmaStudyPlannerPage:
        return AlmaStudyPlannerPage(
            title="Studienplaner Master Informatik",
            page_url="https://alma.example/planner",
            semesters=(),
            modules=(
                AlmaStudyPlannerModule(
                    row_index=1,
                    column_start=1,
                    column_span=1,
                    title="Studienbereich Info Fokus",
                    number="INFO-FOKUS",
                    credits_summary="6/18",
                    credits_earned=6.0,
                    credits_required=18.0,
                    progress_percent=33.3,
                    detail_url=None,
                    is_expandable=True,
                ),
            ),
            view_state=AlmaStudyPlannerViewState(True, True, False),
        )

    def fetch_portal_messages(self) -> AlmaPortalMessagesPage:
        return AlmaPortalMessagesPage(page_url="https://alma.example/start", items=())


class _FakeIlias:
    def fetch_root_page(self):
        return type("Root", (), {"title": "ILIAS", "mainbar_links": (), "top_categories": ()})()

    def fetch_membership_overview(self):
        return ()

    def fetch_task_overview(self):
        return ()


class DashboardStudyProgressTests(unittest.TestCase):
    def test_dashboard_includes_study_planner_progress_and_enrollment_entries(self) -> None:
        dashboard = build_dashboard_payload(
            term_label="Sommer 2026",
            include_course_assignments=False,
            load_alma_client=lambda: _FakeAlma(),
            load_ilias_client=lambda: _FakeIlias(),
            load_mail_panel=lambda *, limit: {"available": True, "items": []},
            load_talks_panel=lambda *, limit: {"available": False, "totalHits": 0, "items": [], "error": None},
            today=datetime(2026, 5, 4).date(),
        )

        self.assertEqual(dashboard["study"]["planner"]["modules"][0]["number"], "INFO-FOKUS")
        self.assertEqual(dashboard["study"]["planner"]["modules"][0]["progress_percent"], 33.3)
        self.assertEqual(dashboard["study"]["enrollments"][0]["status"], "storniert")


if __name__ == "__main__":
    unittest.main()

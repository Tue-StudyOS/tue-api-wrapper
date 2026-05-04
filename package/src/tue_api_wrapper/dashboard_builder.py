from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Callable

from .alma_course_assignments_client import build_timetable_course_assignments
from .alma_course_assignments_models import AlmaTimetableCourseAssignmentsPage
from .alma_portal_messages_client import fetch_portal_messages
from .alma_planner_models import AlmaStudyPlannerPage
from .alma_studyservice_models import AlmaStudyServicePage
from .client import AlmaClient
from .config import AlmaError
from .dashboard_talks import build_talks_panel
from .ilias_client import IliasClient
from .models import (
    AlmaEnrollmentPage,
    AlmaExamNode,
    IliasMembershipItem,
    IliasRootPage,
    IliasTaskItem,
    TimetableResult,
)
from .portal_common import DEFAULT_DASHBOARD_TERM, normalize_dashboard_term, serialize


@dataclass(frozen=True)
class AlmaDashboardData:
    timetable: TimetableResult
    enrollments: AlmaEnrollmentPage
    exams: tuple[AlmaExamNode, ...]
    studyservice_contract: AlmaStudyServicePage
    study_planner: AlmaStudyPlannerPage | None
    study_planner_error: str | None
    studyservice_url: str
    course_assignments: AlmaTimetableCourseAssignmentsPage | None
    current_credit_error: str | None
    portal_messages: dict[str, Any]


@dataclass(frozen=True)
class IliasDashboardData:
    root: IliasRootPage
    memberships: tuple[IliasMembershipItem, ...]
    tasks: tuple[IliasTaskItem, ...]


def build_dashboard_payload(
    *,
    term_label: str = DEFAULT_DASHBOARD_TERM,
    limit: int = 8,
    include_course_assignments: bool = True,
    today: date | None = None,
    load_alma_client: Callable[[], AlmaClient],
    load_ilias_client: Callable[[], IliasClient],
    load_mail_panel: Callable[..., dict[str, Any]],
    load_talks_panel: Callable[..., dict[str, Any]] = build_talks_panel,
) -> dict[str, Any]:
    term_label = normalize_dashboard_term(term_label)
    with ThreadPoolExecutor(max_workers=5, thread_name_prefix="dashboard") as executor:
        alma_future = executor.submit(
            _load_alma_dashboard,
            load_alma_client,
            term_label,
            limit,
            include_course_assignments,
        )
        ilias_future = executor.submit(_load_ilias_dashboard, load_ilias_client, limit)
        mail_future = executor.submit(load_mail_panel, limit=limit)
        talks_future = executor.submit(load_talks_panel, limit=limit)

        alma = alma_future.result()
        ilias = ilias_future.result()
        mail = mail_future.result()
        talks = talks_future.result()

    return _compose_dashboard(alma=alma, ilias=ilias, mail=mail, talks=talks, limit=limit, today=today)


def _load_alma_dashboard(
    load_alma_client: Callable[[], AlmaClient],
    term_label: str,
    limit: int,
    include_course_assignments: bool,
) -> AlmaDashboardData:
    alma = load_alma_client()
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="dashboard-alma") as executor:
        timetable_future = executor.submit(alma.fetch_timetable_for_term, term_label)
        enrollments_future = executor.submit(alma.fetch_enrollment_page)
        exams_future = executor.submit(lambda: tuple(alma.fetch_exam_overview()[:limit]))
        studyservice_future = executor.submit(alma.fetch_studyservice_contract)
        study_planner_future = executor.submit(alma.fetch_study_planner)
        portal_messages_future = executor.submit(_fetch_portal_messages_page, alma)

        timetable = timetable_future.result()
        enrollments = enrollments_future.result()
        exams = exams_future.result()
        studyservice_contract = studyservice_future.result()
        study_planner = None
        study_planner_error = None
        try:
            study_planner = study_planner_future.result()
        except AlmaError as error:
            study_planner_error = str(error)
        try:
            messages = portal_messages_future.result()
            portal_messages = {
                "available": True,
                "sourcePageUrl": messages.page_url,
                "items": serialize(messages.items),
                "error": None,
            }
        except AlmaError as error:
            portal_messages = {"available": False, "sourcePageUrl": None, "items": [], "error": str(error)}

    current_credit_error = None
    if include_course_assignments:
        try:
            course_assignments = build_timetable_course_assignments(alma, timetable, limit=100)
        except AlmaError as error:
            course_assignments = None
            current_credit_error = str(error)
    else:
        course_assignments = None

    return AlmaDashboardData(
        timetable=timetable,
        enrollments=enrollments,
        exams=exams,
        studyservice_contract=studyservice_contract,
        study_planner=study_planner,
        study_planner_error=study_planner_error,
        studyservice_url=alma.studyservice_url,
        course_assignments=course_assignments,
        current_credit_error=current_credit_error,
        portal_messages=portal_messages,
    )


def _load_ilias_dashboard(
    load_ilias_client: Callable[[], IliasClient],
    limit: int,
) -> IliasDashboardData:
    ilias = load_ilias_client()
    return IliasDashboardData(
        root=ilias.fetch_root_page(),
        memberships=tuple(ilias.fetch_membership_overview()[:limit]),
        tasks=tuple(ilias.fetch_task_overview()[:limit]),
    )


def _fetch_portal_messages_page(alma: AlmaClient):
    loader = getattr(alma, "fetch_portal_messages", None)
    if callable(loader):
        return loader()
    return fetch_portal_messages(alma)


def _compose_dashboard(
    *,
    alma: AlmaDashboardData,
    ilias: IliasDashboardData,
    mail: dict[str, Any],
    talks: dict[str, Any],
    limit: int,
    today: date | None,
) -> dict[str, Any]:
    documents = alma.studyservice_contract.reports[:limit]
    upcoming_occurrences = _upcoming_occurrences(alma.timetable.occurrences, today=today)
    passed_exams = [
        exam
        for exam in alma.exams
        if (exam.status or "").strip().upper() in {"BE", "PASSED", "BESTANDEN"}
        or bool(exam.grade and exam.grade.strip() not in {"", "-", "5,0"})
    ]
    credit_values = [
        float((exam.cp or "0").replace(",", "."))
        for exam in alma.exams
        if exam.cp and exam.cp.strip() not in {"", "-"}
    ]
    course_assignments = alma.course_assignments

    metrics = [
        {"label": "Upcoming events", "value": len(upcoming_occurrences)},
        {"label": "Open tasks", "value": len(ilias.tasks)},
        {"label": "Learning spaces", "value": len(ilias.memberships)},
        {"label": "Passed exams", "value": len(passed_exams)},
    ]
    if course_assignments is not None:
        metrics.insert(1, {"label": "Saved semester CP", "value": course_assignments.total_credits})
    if talks["available"]:
        metrics.insert(2, {"label": "Upcoming talks", "value": talks["totalHits"]})

    return {
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "termLabel": alma.timetable.term_label,
        "hero": {
            "title": "Study Hub",
            "subtitle": "Your next classes, open course work, study records, and learning spaces in one place.",
        },
        "metrics": metrics,
        "agenda": {
            "exportUrl": alma.timetable.export_url,
            "items": serialize(upcoming_occurrences),
        },
        "study": {
            "selectedTerm": alma.enrollments.selected_term,
            "message": alma.enrollments.message,
            "passedExamCount": len(passed_exams),
            "trackedCredits": round(sum(credit_values), 1),
            "currentSemesterCredits": course_assignments.total_credits if course_assignments is not None else None,
            "currentSemesterCreditCourses": (
                course_assignments.resolved_credit_count if course_assignments is not None else 0
            ),
            "currentSemesterCreditUnresolved": (
                list(course_assignments.unresolved_credit_summaries) if course_assignments is not None else []
            ),
            "currentSemesterCreditError": alma.current_credit_error,
            "availableTerms": serialize(alma.enrollments.available_terms),
            "enrollments": serialize(alma.enrollments.entries),
            "planner": serialize(alma.study_planner),
            "plannerError": alma.study_planner_error,
        },
        "documents": {
            "reports": serialize(documents),
            "currentDownloadAvailable": alma.studyservice_contract.latest_download_url is not None,
            "currentDownloadUrl": "/api/alma/documents/current"
            if alma.studyservice_contract.latest_download_url is not None
            else None,
            "sourcePageUrl": alma.studyservice_url,
        },
        "exams": serialize(alma.exams),
        "enrollment": serialize(alma.enrollments),
        "ilias": {
            "title": ilias.root.title,
            "mainbarLinks": serialize(ilias.root.mainbar_links),
            "topCategories": serialize(ilias.root.top_categories),
            "memberships": serialize(ilias.memberships),
            "tasks": serialize(ilias.tasks),
        },
        "mail": mail,
        "portalMessages": alma.portal_messages,
        "talks": talks,
        "quickLinks": _quick_links(),
    }


def _upcoming_occurrences(
    occurrences: tuple[Any, ...],
    *,
    today: date | None,
) -> tuple[Any, ...]:
    cutoff = today or datetime.now().date()
    return tuple(item for item in occurrences if (item.end or item.start).date() >= cutoff)


def _quick_links() -> list[dict[str, str]]:
    return [
        {
            "label": "Talks",
            "href": "/talks",
            "description": "Browse upcoming public talks from talks.tuebingen.ai.",
        },
        {
            "label": "Inbox",
            "href": "/mail",
            "description": "Read your Uni mailbox through the same dashboard backend.",
        },
        {
            "label": "Progress",
            "href": "/progress",
            "description": "Review grades, credits, and term-level study status.",
        },
        {
            "label": "Tasks",
            "href": "/tasks",
            "description": "See active ILIAS due items without opening multiple spaces.",
        },
        {
            "label": "Learning spaces",
            "href": "/spaces",
            "description": "Open course, group, and materials spaces from your memberships.",
        },
        {
            "label": "Documents",
            "href": "/documents",
            "description": "Access Alma study-service PDFs and report jobs.",
        },
    ]

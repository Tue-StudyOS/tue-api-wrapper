from __future__ import annotations
from dataclasses import dataclass
from ..alma_catalog_client import fetch_course_catalog_page
from ..alma_course_assignments_client import fetch_timetable_course_assignments
from ..alma_course_registration_client import (
    inspect_course_registration_support,
    prepare_course_registration,
    register_for_course,
)
from ..alma_course_search_client import search_courses
from ..alma_feature_client import fetch_current_lectures
from ..alma_official_documents import download_exam_report, download_studyservice_report, list_exam_reports
from ..alma_portal_messages_client import fetch_portal_messages, fetch_portal_messages_feed, refresh_portal_messages_feed
from ..alma_planner_client import fetch_study_planner
from ..alma_timetable_client import fetch_timetable_controls, fetch_timetable_view, refresh_timetable_export_url
from ..client import AlmaClient
from ..course_discovery_service import CourseDiscoveryService
from ..ilias_actions_client import add_to_favorites, inspect_waitlist_support, join_waitlist
from ..ilias_client import IliasClient
from ..ilias_feature_client import fetch_ilias_info_page, fetch_ilias_search_filters, search_ilias
from ..mail_client import MailClient
from ..moodle_client import MoodleClient
from .credentials import UniversityCredentials
from .discovery import CourseDiscoveryApi
from .portal import AuthenticatedPortalApi
from .praxisportal import AuthenticatedPraxisportalApi
from .public import TuebingenPublicClient

@dataclass(slots=True)
class AuthenticatedAlmaApi:
    credentials: UniversityCredentials
    _client: AlmaClient | None = None

    @property
    def client(self) -> AlmaClient:
        if self._client is None:
            client = AlmaClient()
            client.login(self.credentials.username, self.credentials.password)
            self._client = client
        return self._client

    def timetable(self, term: str):
        return self.client.fetch_timetable_for_term(term)

    def timetable_controls(self):
        return fetch_timetable_controls(self.client)

    def timetable_view(
        self,
        *,
        term: str | None = None,
        week: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        single_day: str | None = None,
        limit: int | None = None,
    ):
        return fetch_timetable_view(
            self.client,
            term=term,
            week=week,
            from_date=from_date,
            to_date=to_date,
            single_day=single_day,
            limit=limit,
        )

    def refresh_timetable_export_url(self, *, term: str | None = None):
        return refresh_timetable_export_url(self.client, term=term)

    def timetable_course_assignments(self, term: str, *, limit: int | None = None):
        return fetch_timetable_course_assignments(self.client, term=term, limit=limit)

    def current_lectures(self, *, date: str | None = None, limit: int | None = 50):
        return fetch_current_lectures(self.client, date=date, limit=limit)

    def course_offerings(self, *, query: str = "", term: str | None = None, limit: int | None = 20):
        return search_courses(self.client, query=query, term=term, limit=limit)

    def course_registration_support(self, detail_url: str):
        return inspect_course_registration_support(self.client, detail_url)

    def course_registration_options(self, detail_url: str):
        return prepare_course_registration(self.client, detail_url)

    def register_for_course(self, detail_url: str, *, planelement_id: str | None = None):
        return register_for_course(self.client, detail_url, planelement_id=planelement_id)

    def catalog_page(self, *, term: str | None = None, limit: int = 80):
        return fetch_course_catalog_page(self.client, term=term, limit=limit)

    def study_planner(self):
        return fetch_study_planner(self.client)

    def portal_messages_feed(self):
        return fetch_portal_messages_feed(self.client)

    def portal_messages(self):
        return fetch_portal_messages(self.client)

    def refresh_portal_messages_feed(self):
        return refresh_portal_messages_feed(self.client)

    def exams(self):
        return self.client.fetch_exam_overview()

    def exam_reports(self):
        return list_exam_reports(self.client)

    def download_exam_report(self, *, trigger_name: str | None = None):
        return download_exam_report(self.client, trigger_name=trigger_name)

    def enrollments(self):
        return self.client.fetch_enrollment_page()

    def documents(self):
        return self.client.list_studyservice_reports()

    def document_reports(self):
        return self.documents()

    def studyservice_documents(self):
        return self.client.fetch_studyservice_contract()

    def studyservice_summary(self):
        return self.client.fetch_studyservice_contract()

    def download_current_document(self):
        return self.client.download_current_studyservice_document()

    def download_document(self, doc_id: str):
        return self.client.download_document_by_id(doc_id)

    def download_studyservice_report(self, *, trigger_name: str | None = None, term_id: str | None = None):
        return download_studyservice_report(self.client, trigger_name=trigger_name, term_id=term_id)

@dataclass(slots=True)
class AuthenticatedIliasApi:
    credentials: UniversityCredentials
    _client: IliasClient | None = None

    @property
    def client(self) -> IliasClient:
        if self._client is None:
            client = IliasClient()
            client.login(self.credentials.username, self.credentials.password)
            self._client = client
        return self._client

    def root(self):
        return self.client.fetch_root_page()

    def memberships(self):
        return self.client.fetch_membership_overview()

    def tasks(self):
        return self.client.fetch_task_overview()

    def content(self, target: str):
        return self.client.fetch_content_page(target)

    def forum_topics(self, target: str):
        return self.client.fetch_forum_topics(target)

    def exercise_assignments(self, target: str):
        return self.client.fetch_exercise_assignments(target)

    def course_assignments(self, target: str):
        return self.client.fetch_course_assignments(target)

    def assignment_deadlines(self, *, course_limit: int = 20, assignment_limit: int = 50):
        return self.client.fetch_assignment_deadlines(course_limit=course_limit, assignment_limit=assignment_limit)
    def search_filters(self):
        return fetch_ilias_search_filters(self.client)

    def search(self, term: str, *, page: int = 1):
        return search_ilias(self.client, term=term, page=page)

    def info(self, target: str):
        return fetch_ilias_info_page(self.client, target=target)

    def add_favorite(self, url: str):
        return add_to_favorites(self.client, url=url)

    def waitlist_support(self, url: str):
        return inspect_waitlist_support(self.client, url=url)

    def join_waitlist(self, url: str, *, accept_agreement: bool = False):
        return join_waitlist(self.client, url=url, accept_agreement=accept_agreement)

@dataclass(slots=True)
class AuthenticatedMoodleApi:
    credentials: UniversityCredentials
    _client: MoodleClient | None = None

    @property
    def client(self) -> MoodleClient:
        if self._client is None:
            client = MoodleClient()
            client.login(self.credentials.username, self.credentials.password)
            self._client = client
        return self._client

    def dashboard(self, *, event_limit: int = 6, course_limit: int = 12, recent_limit: int = 9):
        return self.client.fetch_dashboard(
            event_limit=event_limit,
            course_limit=course_limit,
            recent_limit=recent_limit,
        )

    def deadlines(self, *, days: int = 30, limit: int = 50):
        return self.client.fetch_calendar(days=days, limit=limit)

    def courses(self, *, classification: str = "all", limit: int = 24, offset: int = 0):
        return self.client.fetch_enrolled_courses(classification=classification, limit=limit, offset=offset)

    def categories(self, *, category_id: int | None = None):
        return self.client.fetch_category_page(category_id)

    def course(self, course_id: int):
        return self.client.fetch_course_detail(course_id)

    def enrol_in_course(self, course_id: int, *, enrolment_key: str | None = None):
        return self.client.enrol_in_course(course_id, enrolment_key=enrolment_key)

    def grades(self):
        return self.client.fetch_grades()

    def messages(self):
        return self.client.fetch_messages()

    def notifications(self):
        return self.client.fetch_notifications()


@dataclass(slots=True)
class AuthenticatedMailApi:
    credentials: UniversityCredentials
    _client: MailClient | None = None

    @property
    def client(self) -> MailClient:
        if self._client is None:
            client = MailClient()
            client.login(self.credentials.username, self.credentials.password)
            self._client = client
        return self._client

    def inbox(self, *, limit: int = 12):
        return self.client.fetch_inbox_summary(limit=limit)

    def mailbox(self, *, name: str = "INBOX", limit: int = 12, unread_only: bool = False, query: str = ""):
        return self.client.fetch_mailbox_summary(
            mailbox=name,
            limit=limit,
            unread_only=unread_only,
            query=query,
        )

    def mailboxes(self):
        return self.client.list_mailboxes()

    def message(self, uid: str, *, mailbox: str = "INBOX"):
        return self.client.fetch_message_detail(uid, mailbox=mailbox)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


class TuebingenAuthenticatedClient:
    def __init__(self, credentials: UniversityCredentials) -> None:
        self.credentials = credentials
        self.public = TuebingenPublicClient()
        self.alma = AuthenticatedAlmaApi(credentials)
        self.ilias = AuthenticatedIliasApi(credentials)
        self.moodle = AuthenticatedMoodleApi(credentials)
        self.mail = AuthenticatedMailApi(credentials)
        self.praxisportal = AuthenticatedPraxisportalApi(credentials)
        self.portal = AuthenticatedPortalApi(self)
        self.discovery = CourseDiscoveryApi(
            CourseDiscoveryService(
                alma_loader=lambda: self.alma.client,
                ilias_loader=lambda: self.ilias.client,
            )
        )

    @classmethod
    def login(
        cls,
        *,
        username: str,
        password: str,
    ) -> "TuebingenAuthenticatedClient":
        return cls(UniversityCredentials(username, password))

    def close(self) -> None:
        self.mail.close()

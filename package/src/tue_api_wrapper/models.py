from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from .calendar_room_models import CalendarRoomDetails
from .alma_enrollment_models import AlmaEnrollmentEntry


@dataclass(frozen=True)
class LoginForm:
    action_url: str
    payload: dict[str, str]


@dataclass(frozen=True)
class CalendarEvent:
    summary: str
    start: date | datetime
    end: date | datetime | None
    location: str | None
    description: str | None
    uid: str | None
    recurrence_rule: str | None
    excluded_starts: tuple[date | datetime, ...]
    room_details: CalendarRoomDetails | None = None


@dataclass(frozen=True)
class CalendarOccurrence:
    summary: str
    start: datetime
    end: datetime | None
    location: str | None
    description: str | None
    room_details: CalendarRoomDetails | None = None
    uid: str | None = None
    status: Literal["cancelled"] | None = None
    cancellation_reason: str | None = None


@dataclass(frozen=True)
class TimetableResult:
    term_label: str
    term_id: str
    export_url: str
    raw_ics: str
    events: tuple[CalendarEvent, ...]
    occurrences: tuple[CalendarOccurrence, ...]
    available_terms: dict[str, str]


@dataclass(frozen=True)
class AlmaEnrollmentPage:
    selected_term: str | None
    available_terms: dict[str, str]
    message: str | None
    entries: tuple[AlmaEnrollmentEntry, ...] = ()


@dataclass(frozen=True)
class AlmaExamNode:
    level: int
    kind: str | None
    title: str
    number: str | None
    attempt: str | None
    grade: str | None
    cp: str | None
    malus: str | None
    status: str | None
    free_trial: str | None
    remark: str | None
    exception: str | None
    release_date: str | None


@dataclass(frozen=True)
class AlmaCourseCatalogNode:
    level: int
    kind: str | None
    title: str
    description: str | None
    permalink: str | None
    expandable: bool


@dataclass(frozen=True)
class AlmaModuleSearchResult:
    number: str | None
    title: str
    element_type: str | None
    detail_url: str | None = None


@dataclass(frozen=True)
class AlmaDocumentReport:
    label: str
    trigger_name: str


@dataclass(frozen=True)
class AlmaModuleSearchForm:
    action_url: str
    payload: dict[str, str]
    query_field_name: str


@dataclass(frozen=True)
class AlmaModuleSearchPage:
    form: AlmaModuleSearchForm
    results: tuple[AlmaModuleSearchResult, ...]


@dataclass(frozen=True)
class AlmaSearchOption:
    value: str
    label: str


@dataclass(frozen=True)
class AlmaModuleSearchFilters:
    element_types: tuple[AlmaSearchOption, ...]
    languages: tuple[AlmaSearchOption, ...]
    degrees: tuple[AlmaSearchOption, ...]
    subjects: tuple[AlmaSearchOption, ...]
    faculties: tuple[AlmaSearchOption, ...]


@dataclass(frozen=True)
class AlmaModuleSearchFieldMap:
    query: str
    title: str | None
    number: str | None
    element_type: str | None
    language: str | None
    degree: str | None
    subject: str | None
    faculty: str | None


@dataclass(frozen=True)
class AlmaAdvancedModuleSearchForm:
    action_url: str
    payload: dict[str, str]
    query_field_name: str
    search_button_name: str
    toggle_advanced_button_name: str | None
    fields: AlmaModuleSearchFieldMap
    filters: AlmaModuleSearchFilters


@dataclass(frozen=True)
class AlmaModuleSearchResponse:
    results: tuple[AlmaModuleSearchResult, ...]
    total_results: int | None
    returned_results: int
    total_pages: int | None
    truncated: bool


@dataclass(frozen=True)
class AlmaModuleSearchResultsPage:
    action_url: str | None
    payload: dict[str, str]
    results: tuple[AlmaModuleSearchResult, ...]
    total_results: int | None
    total_pages: int | None
    rows_input_name: str | None
    rows_refresh_name: str | None


@dataclass(frozen=True)
class AlmaDetailField:
    label: str
    value: str


@dataclass(frozen=True)
class AlmaDetailSection:
    title: str
    fields: tuple[AlmaDetailField, ...]


@dataclass(frozen=True)
class AlmaDetailTable:
    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class AlmaModuleDetail:
    title: str
    number: str | None
    permalink: str | None
    source_url: str
    active_tab: str | None
    available_tabs: tuple[str, ...]
    sections: tuple[AlmaDetailSection, ...]
    module_study_program_tables: tuple[AlmaDetailTable, ...]


@dataclass(frozen=True)
class AlmaDownloadedDocument:
    source_url: str
    final_url: str
    filename: str
    content_type: str | None
    data: bytes


@dataclass(frozen=True)
class IliasLink:
    label: str
    url: str


@dataclass(frozen=True)
class IliasLoginForm:
    action_url: str
    payload: dict[str, str]


@dataclass(frozen=True)
class IliasRootPage:
    title: str
    mainbar_links: tuple[IliasLink, ...]
    top_categories: tuple[IliasLink, ...]


@dataclass(frozen=True)
class IliasContentItem:
    label: str
    url: str
    kind: str | None
    properties: tuple[str, ...]


@dataclass(frozen=True)
class IliasContentSection:
    label: str
    items: tuple[IliasContentItem, ...]


@dataclass(frozen=True)
class IliasContentPage:
    title: str
    page_url: str
    sections: tuple[IliasContentSection, ...]


@dataclass(frozen=True)
class IliasMembershipItem:
    title: str
    url: str
    kind: str | None
    description: str | None
    info_url: str | None
    properties: tuple[str, ...]


@dataclass(frozen=True)
class IliasTaskItem:
    title: str
    url: str
    item_type: str | None
    start: str | None
    end: str | None


@dataclass(frozen=True)
class IliasForumTopic:
    title: str
    url: str
    author: str | None
    posts: str | None
    last_post: str | None
    visits: str | None


@dataclass(frozen=True)
class IliasExerciseAssignment:
    title: str
    url: str
    due_hint: str | None
    due_at: str | None
    requirement: str | None
    last_submission: str | None
    submission_type: str | None
    status: str | None
    team_action_url: str | None

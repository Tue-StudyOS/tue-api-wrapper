from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from .alma_catalog_client import fetch_course_catalog_page
from .alma_course_search_client import search_courses
from .alma_feature_client import fetch_current_lectures
from .alma_portal_messages_client import fetch_portal_messages, fetch_portal_messages_feed, refresh_portal_messages_feed
from .alma_planner_client import fetch_study_planner
from .alma_timetable_client import (
    fetch_timetable_controls,
    fetch_timetable_view,
    refresh_timetable_export_url,
)
from .alma_timetable_pdf import render_timetable_pdf
from .api_errors import translate_alma_error
from .client import AlmaClient
from .config import AlmaError, AlmaParseError
from .course_detail_linking import build_unified_course_detail, resolve_alma_course_detail
from .ilias_feature_client import fetch_ilias_info_page, fetch_ilias_search_filters, search_ilias
from .moodle_auth import build_moodle_client
from .portal_service import PortalService, normalize_dashboard_term, serialize

router = APIRouter()
portal_service = PortalService()


def _alma_client():
    return portal_service._alma_client()


def _ilias_client():
    return portal_service._ilias_client()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


def _studyservice_summary(client: AlmaClient) -> dict[str, object]:
    contract = client.fetch_studyservice_contract()
    return {
        "bannerText": contract.banner_text,
        "personName": contract.person_name,
        "activeTabLabel": contract.active_tab_label,
        "tabs": serialize(contract.tabs),
        "outputRequests": serialize(contract.output_requests),
        "reports": serialize(contract.reports),
        "currentDownloadAvailable": contract.latest_download_url is not None,
        "currentDownloadUrl": "/api/alma/documents/current" if contract.latest_download_url is not None else None,
        "sourcePageUrl": client.studyservice_url,
    }


@router.get("/api/course-detail")
def unified_course_detail(
    url: str = "",
    title: str = "",
    term: str = "",
    ilias_limit: int = Query(8, ge=1, le=20),
) -> dict[str, object]:
    try:
        authenticated_alma = None
        alma_error = None
        try:
            authenticated_alma = _alma_client()
        except AlmaError as error:
            alma_error = str(error)

        if not url.strip() and title.strip() and authenticated_alma is None and alma_error:
            raise AlmaParseError(alma_error)

        detail = resolve_alma_course_detail(
            authenticated_alma or AlmaClient(),
            detail_url=url,
            title=title,
            term=term.strip() or None,
            search_client=authenticated_alma if not url.strip() else None,
        )
        ilias_client = None
        ilias_error = None
        try:
            ilias_client = _ilias_client()
        except AlmaError as error:
            ilias_error = str(error)
        moodle_client = None
        moodle_error = None
        try:
            moodle_client = build_moodle_client()
        except AlmaError as error:
            moodle_error = str(error)

        return serialize(
            build_unified_course_detail(
                detail,
                ilias_client=ilias_client,
                ilias_error=ilias_error,
                ilias_limit=ilias_limit,
                alma_client=authenticated_alma,
                alma_error=alma_error,
                moodle_client=moodle_client,
                moodle_error=moodle_error,
            )
        )
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/current-lectures")
def alma_current_lectures(date: str = "", limit: int = Query(50, ge=1, le=200)) -> dict[str, object]:
    try:
        page = fetch_current_lectures(
            _alma_client(),
            date=date.strip() or None,
            limit=limit,
        )
        return serialize(page)
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/timetable/controls")
def alma_timetable_controls() -> dict[str, object]:
    try:
        return serialize(fetch_timetable_controls(_alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/timetable/view")
def alma_timetable_view(
    term: str = "",
    week: str = "",
    from_date: str = "",
    to_date: str = "",
    single_day: str = "",
    limit: int = Query(200, ge=1, le=2000),
) -> dict[str, object]:
    try:
        view = fetch_timetable_view(
            _alma_client(),
            term=normalize_dashboard_term(term),
            week=week.strip() or None,
            from_date=from_date.strip() or None,
            to_date=to_date.strip() or None,
            single_day=single_day.strip() or None,
            limit=limit,
        )
        return serialize(view)
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/timetable/export-url/refresh")
def alma_timetable_export_refresh(term: str = "") -> dict[str, object]:
    try:
        return serialize(refresh_timetable_export_url(_alma_client(), term=term.strip() or None))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/portal-messages/feed")
def alma_portal_messages_feed() -> dict[str, object]:
    try:
        return serialize(fetch_portal_messages_feed(_alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/portal-messages")
def alma_portal_messages() -> dict[str, object]:
    try:
        return serialize(fetch_portal_messages(_alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/portal-messages/feed/refresh")
def alma_portal_messages_feed_refresh() -> dict[str, object]:
    try:
        return serialize(refresh_portal_messages_feed(_alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/timetable/pdf")
def alma_timetable_pdf(
    term: str = "",
    week: str = "",
    from_date: str = "",
    to_date: str = "",
    single_day: str = "",
) -> Response:
    try:
        pdf = render_timetable_pdf(
            _alma_client(),
            term=term.strip() or None,
            week=week.strip() or None,
            from_date=from_date.strip() or None,
            to_date=to_date.strip() or None,
            single_day=single_day.strip() or None,
        )
    except AlmaError as error:
        raise _translate_error(error) from error

    return Response(
        content=pdf.data,
        media_type=pdf.content_type,
        headers={"Content-Disposition": f'inline; filename="{pdf.filename}"'},
    )


@router.get("/api/alma/study-planner")
def alma_study_planner() -> dict[str, object]:
    try:
        return serialize(fetch_study_planner(_alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/course-search")
def alma_course_search(
    query: str = "",
    term: str = "",
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, object]:
    try:
        return serialize(search_courses(_alma_client(), query=query, term=term.strip() or None, limit=limit))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/catalog/page")
def alma_catalog_page(
    term: str = "",
    limit: int = Query(80, ge=1, le=400),
) -> dict[str, object]:
    try:
        return serialize(fetch_course_catalog_page(_alma_client(), term=term.strip() or None, limit=limit))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/studyservice/summary")
def alma_studyservice_summary() -> dict[str, object]:
    try:
        return _studyservice_summary(_alma_client())
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/search")
def ilias_search(
    term: str,
    page: int = Query(1, ge=1, le=50),
    search_mode: str = "",
    content_type: list[str] = Query(default=[]),
    created_enabled: bool = False,
    created_mode: str = "",
    created_date: str = "",
) -> dict[str, object]:
    try:
        return serialize(
            search_ilias(
                _ilias_client(),
                term=term,
                page=page,
                search_mode=search_mode.strip() or None,
                content_types=tuple(content_type),
                created_enabled=created_enabled,
                created_mode=created_mode.strip() or None,
                created_date=created_date.strip() or None,
            )
        )
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/search/options")
def ilias_search_options() -> dict[str, object]:
    try:
        return serialize(fetch_ilias_search_filters(_ilias_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/info")
def ilias_info(target: str) -> dict[str, object]:
    try:
        return serialize(fetch_ilias_info_page(_ilias_client(), target=target))
    except AlmaError as error:
        raise _translate_error(error) from error

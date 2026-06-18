from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from .alma_official_documents import (
    download_exam_report,
    download_studyservice_report,
    list_exam_reports,
)
from .api_errors import translate_alma_error
from .config import AlmaError
from .ilias_actions_client import add_to_favorites, inspect_waitlist_support, join_waitlist
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


def _pdf_response(document) -> Response:
    return Response(
        content=document.data,
        media_type=document.content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{document.filename}"'},
    )


@router.get("/api/alma/exams/reports")
def alma_exam_reports() -> list[object]:
    try:
        return serialize(list_exam_reports(portal_service._alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/exams/report")
def alma_exam_report(trigger_name: str = "") -> Response:
    return _download_exam_report_response(trigger_name)


@router.get("/api/alma/exams/report")
def alma_exam_report_get(trigger_name: str = "") -> Response:
    return _download_exam_report_response(trigger_name)


def _download_exam_report_response(trigger_name: str = "") -> Response:
    try:
        document = download_exam_report(
            portal_service._alma_client(),
            trigger_name=trigger_name.strip() or None,
        )
        return _pdf_response(document)
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/studyservice/report")
def alma_studyservice_report(trigger_name: str = "", term_id: str = "") -> Response:
    try:
        document = download_studyservice_report(
            portal_service._alma_client(),
            trigger_name=trigger_name.strip() or None,
            term_id=term_id.strip() or None,
        )
        return _pdf_response(document)
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/enrollments/reports")
def alma_enrollment_reports() -> list[object]:
    try:
        return serialize(portal_service._alma_client().list_enrollment_reports())
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/enrollments/report")
def alma_enrollment_report(trigger_name: str = "", term: str = "") -> Response:
    return _download_enrollment_report_response(trigger_name, term)


@router.get("/api/alma/enrollments/report")
def alma_enrollment_report_get(trigger_name: str = "", term: str = "") -> Response:
    return _download_enrollment_report_response(trigger_name, term)


def _download_enrollment_report_response(trigger_name: str = "", term: str = "") -> Response:
    try:
        document = portal_service._alma_client().download_enrollment_report(
            trigger_name=trigger_name.strip() or None,
            term=term.strip() or None,
        )
        return _pdf_response(document)
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/ilias/favorites")
def ilias_add_favorite(url: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        result = serialize(add_to_favorites(portal_service._ilias_client(), url=url))
        portal_service.invalidate_portal_cache()
        return result
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/waitlist/support")
def ilias_waitlist_support(url: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        return serialize(inspect_waitlist_support(portal_service._ilias_client(), url=url))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/ilias/waitlist/join")
def ilias_waitlist_join(
    url: str = Query(..., min_length=1),
    accept_agreement: bool = False,
) -> dict[str, object]:
    try:
        result = serialize(
            join_waitlist(
                portal_service._ilias_client(),
                url=url,
                accept_agreement=accept_agreement,
            )
        )
        portal_service.invalidate_portal_cache()
        return result
    except AlmaError as error:
        raise _translate_error(error) from error

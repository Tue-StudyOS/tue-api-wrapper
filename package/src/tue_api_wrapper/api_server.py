from __future__ import annotations

import os
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn

from .alma_catalog_client import fetch_course_catalog_page
from .api_errors import alma_error_status_code, translate_alma_error
from .api_routes_alma_assignments import router as alma_assignments_router
from .api_routes_alma_registration import router as alma_registration_router
from .api_routes_discovery import router as discovery_router
from .api_routes_edit_actions import router as edit_actions_router
from .api_routes_extended import router as extended_router
from .api_routes_ilias import router as ilias_router
from .api_routes_mail import router as mail_router
from .api_routes_moodle import router as moodle_router
from .api_routes_products import router as products_router
from .client import AlmaClient
from .config import AlmaError
from .portal_service import DEFAULT_DASHBOARD_TERM, PortalService, normalize_dashboard_term, serialize

app = FastAPI(
    title="tue-api-wrapper",
    version="0.2.2",
    description="Unified Alma and ILIAS backend for CLI, web, and ChatGPT surfaces.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    alma_assignments_router,
    alma_registration_router,
    discovery_router,
    edit_actions_router,
    extended_router,
    ilias_router,
    mail_router,
    moodle_router,
    products_router,
):
    app.include_router(router)

portal_service = PortalService()


def _alma_client() -> AlmaClient:
    return portal_service._alma_client()


def _public_alma_client() -> AlmaClient:
    return AlmaClient()


def _translate_error(error: AlmaError) -> HTTPException:
    return translate_alma_error(error)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "tue-api-wrapper",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(
    term: str = Query(DEFAULT_DASHBOARD_TERM),
    include_course_assignments: bool = Query(True),
) -> dict[str, object]:
    try:
        return portal_service.build_dashboard(
            term_label=term,
            include_course_assignments=include_course_assignments,
        )
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/search")
def search(query: str, term: str = Query(DEFAULT_DASHBOARD_TERM)) -> dict[str, object]:
    try:
        return {"results": portal_service.search(query, term_label=term)}
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/items/{item_id:path}")
def fetch_item(item_id: str, term: str = Query(DEFAULT_DASHBOARD_TERM)) -> dict[str, object]:
    try:
        return portal_service.fetch_item(item_id, term_label=term)
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/alma/timetable")
def alma_timetable(term: str = Query(DEFAULT_DASHBOARD_TERM)) -> dict[str, object]:
    try:
        result = _alma_client().fetch_timetable_for_term(normalize_dashboard_term(term))
        return serialize(result)
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/alma/enrollments")
def alma_enrollments() -> dict[str, object]:
    try:
        return serialize(_alma_client().fetch_enrollment_page())
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/alma/exams")
def alma_exams(limit: int = Query(20, ge=1, le=100)) -> list[object]:
    try:
        return serialize(_alma_client().fetch_exam_overview()[:limit])
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/alma/catalog")
def alma_catalog(term: str = "", limit: int = Query(20, ge=1, le=100)) -> list[object]:
    try:
        page = fetch_course_catalog_page(_alma_client(), term=term.strip() or None, limit=limit)
        return serialize(page.nodes)
    except AlmaError as error:
        raise _translate_error(error) from error

@app.get("/api/alma/module-search")
def alma_module_search(
    query: str = "",
    title: str = "",
    number: str = "",
    element_type: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    degree: list[str] = Query(default=[]),
    subject: list[str] = Query(default=[]),
    faculty: list[str] = Query(default=[]),
    max_results: int = Query(100, ge=1, le=300),
) -> dict[str, object]:
    try:
        result = _public_alma_client().search_public_module_descriptions(
            query=query,
            title=title,
            number=number,
            element_types=tuple(element_type),
            languages=tuple(language),
            degrees=tuple(degree),
            subjects=tuple(subject),
            faculties=tuple(faculty),
            max_results=max_results,
        )
        return {
            "results": serialize(result.results),
            "returnedResults": result.returned_results,
            "totalResults": result.total_results,
            "totalPages": result.total_pages,
            "truncated": result.truncated,
            "sourcePageUrl": _public_alma_client().public_module_search_url,
        }
    except AlmaError as error:
        raise _translate_error(error) from error


@app.get("/api/alma/module-search/filters")
def alma_module_search_filters() -> dict[str, object]:
    try:
        filters = _public_alma_client().fetch_public_module_search_filters()
        return {
            "sourcePageUrl": _public_alma_client().public_module_search_url,
            "filters": {
                "elementTypes": serialize(filters.element_types),
                "languages": serialize(filters.languages),
                "degrees": serialize(filters.degrees),
                "subjects": serialize(filters.subjects),
                "faculties": serialize(filters.faculties),
            },
        }
    except AlmaError as error:
        raise _translate_error(error) from error


@app.get("/api/alma/module-detail")
def alma_module_detail(url: str) -> dict[str, object]:
    try:
        return serialize(_public_alma_client().fetch_public_module_detail(url))
    except AlmaError as error:
        raise _translate_error(error) from error


@app.get("/api/alma/documents")
def alma_documents() -> list[object]:
    try:
        return serialize(_alma_client().list_studyservice_reports())
    except AlmaError as error:
        raise _translate_error(error) from error


@app.get("/api/alma/studyservice")
def alma_studyservice() -> dict[str, object]:
    try:
        contract = _alma_client().fetch_studyservice_contract()
        return {
            "reports": serialize(contract.reports),
            "currentDownloadAvailable": contract.latest_download_url is not None,
            "currentDownloadUrl": "/api/alma/documents/current"
            if contract.latest_download_url is not None
            else None,
            "sourcePageUrl": _alma_client().studyservice_url,
        }
    except AlmaError as error:
        raise _translate_error(error) from error


@app.get("/api/alma/documents/current")
def alma_current_document() -> Response:
    try:
        document = _alma_client().download_current_studyservice_document()
    except AlmaError as error:
        raise _translate_error(error) from error

    return Response(
        content=document.data,
        media_type=document.content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{document.filename}"'},
    )


@app.get("/api/alma/documents/{doc_id}")
def alma_document_by_id(doc_id: str) -> Response:
    try:
        document = _alma_client().download_document_by_id(doc_id)
    except AlmaError as error:
        raise _translate_error(error) from error

    return Response(
        content=document.data,
        media_type=document.content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{document.filename}"'},
    )


@app.get("/api/alma/documents/{doc_id}/download-url")
def alma_document_download_url(doc_id: str) -> dict[str, str]:
    return {"url": f"/api/alma/documents/{quote(doc_id, safe='')}"}


@app.exception_handler(AlmaError)
async def handle_alma_error(_request, error: AlmaError) -> JSONResponse:
    return JSONResponse(status_code=alma_error_status_code(error), content={"detail": str(error)})


def main() -> None:
    uvicorn.run(
        "tue_api_wrapper.api_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import Response

from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


def _alma_client():
    return portal_service._alma_client()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


@router.get("/api/alma/documents")
def alma_documents() -> list[object]:
    try:
        return serialize(_alma_client().list_studyservice_reports())
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/studyservice")
def alma_studyservice() -> dict[str, object]:
    try:
        client = _alma_client()
        contract = client.fetch_studyservice_contract()
        return {
            "reports": serialize(contract.reports),
            "currentDownloadAvailable": contract.latest_download_url is not None,
            "currentDownloadUrl": "/api/alma/documents/current" if contract.latest_download_url is not None else None,
            "sourcePageUrl": client.studyservice_url,
        }
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/alma/documents/current")
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


@router.get("/api/alma/documents/{doc_id}")
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


@router.get("/api/alma/documents/{doc_id}/download-url")
def alma_document_download_url(doc_id: str) -> dict[str, str]:
    return {"url": f"/api/alma/documents/{quote(doc_id, safe='')}"}

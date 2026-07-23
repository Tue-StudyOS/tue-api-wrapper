from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, SecretStr

from .portal_service import serialize
from .ppi_auth import PpiConfigurationError, build_ppi_client
from .ppi_client import (
    PpiAccessError,
    PpiAuthenticationError,
    PpiClient,
    PpiError,
    PpiValidationError,
)

router = APIRouter()


class PpiSignupRequest(BaseModel):
    username: str = Field(min_length=7, max_length=7)
    password: SecretStr = Field(min_length=1, max_length=256)


class PpiTokenRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def _public_client() -> PpiClient:
    return PpiClient()


def _authenticated_client() -> PpiClient:
    return build_ppi_client()


def _translate_ppi_error(error: Exception) -> HTTPException:
    if isinstance(error, PpiConfigurationError):
        status_code = 503
    elif isinstance(error, PpiAuthenticationError):
        status_code = 401
    elif isinstance(error, PpiAccessError):
        status_code = 403
    elif isinstance(error, PpiValidationError):
        status_code = 400
    elif isinstance(error, (PpiError, requests.RequestException)):
        status_code = 502
    else:  # pragma: no cover - callers only pass supported errors
        status_code = 500
    return HTTPException(status_code=status_code, detail=str(error))


@router.post("/api/ppi/signup", status_code=201)
def ppi_signup(request: PpiSignupRequest) -> dict[str, object]:
    client = _public_client()
    try:
        return serialize(client.signup(request.username, request.password.get_secret_value()))
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        client.close()


@router.get("/api/ppi/lectures")
def ppi_lectures() -> dict[str, object]:
    client = None
    try:
        client = _authenticated_client()
        return serialize(client.fetch_lecture_catalog())
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        if client is not None:
            client.close()


@router.get("/api/ppi/borrowed")
def ppi_borrowed() -> dict[str, object]:
    client = None
    try:
        client = _authenticated_client()
        return serialize(client.fetch_borrowed_lectures())
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        if client is not None:
            client.close()


@router.post("/api/ppi/lectures/{lecture_id}/borrow")
def ppi_borrow(lecture_id: int) -> dict[str, object]:
    client = None
    try:
        client = _authenticated_client()
        return serialize(client.borrow_lecture(lecture_id))
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        if client is not None:
            client.close()


@router.get("/api/ppi/lectures/{lecture_id}/download")
def ppi_download(lecture_id: int) -> Response:
    client = None
    try:
        client = _authenticated_client()
        download = client.download_lecture(lecture_id)
        filename = download.filename.replace('"', "").replace("\r", "").replace("\n", "")
        return Response(
            content=download.data,
            media_type=download.content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        if client is not None:
            client.close()


@router.post("/api/ppi/token-requests")
def ppi_token_request(request: PpiTokenRequest) -> dict[str, object]:
    client = None
    try:
        client = _authenticated_client()
        return serialize(client.request_tokens(request.message))
    except (PpiError, requests.RequestException) as error:
        raise _translate_ppi_error(error) from error
    finally:
        if client is not None:
            client.close()

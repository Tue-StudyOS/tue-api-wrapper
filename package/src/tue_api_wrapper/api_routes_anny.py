from __future__ import annotations

import requests
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from .anny_client import AnnyClient, DEFAULT_ANNY_ORGANIZATION_SLUG
from .portal_service import serialize

router = APIRouter()
anny_client = AnnyClient()


class AnnyQuoteRequest(BaseModel):
    resource_id: str
    service_id: str
    start_date: str
    end_date: str


def _translate_anny_error(error: Exception) -> HTTPException:
    status_code = 502 if isinstance(error, requests.RequestException) else 400
    return HTTPException(status_code=status_code, detail=str(error))


def _client(customer_account_id: str | None, organization_slug: str, authorization: str | None = None) -> AnnyClient:
    if customer_account_id or authorization:
        return AnnyClient(customer_account_id=customer_account_id, organization_slug=organization_slug, auth_token=authorization)
    if organization_slug == DEFAULT_ANNY_ORGANIZATION_SLUG:
        return anny_client
    return AnnyClient(organization_slug=organization_slug)


def _default_client(authorization: str | None = None) -> AnnyClient:
    return AnnyClient(auth_token=authorization) if authorization else anny_client


@router.get("/api/anny/resources")
def anny_resources(
    query: str = Query("", max_length=120),
    organization_slug: str = Query(DEFAULT_ANNY_ORGANIZATION_SLUG, max_length=120),
    customer_account_id: str | None = Query(None, max_length=80),
    category_id: str = Query("596", max_length=40),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    authorization: str | None = Header(None),
) -> dict[str, object]:
    try:
        return serialize(
            _client(customer_account_id, organization_slug, authorization).list_resources(
                query=query,
                category_id=category_id,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{slug}")
def anny_resource(
    slug: str,
    visit_token: str | None = Query(None, max_length=120),
    authorization: str | None = Header(None),
) -> dict[str, object]:
    try:
        return serialize(_default_client(authorization).fetch_resource(slug, visit_token=visit_token))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/service-configuration")
def anny_service_configuration(
    resource_id: str,
    service_id: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> dict[str, object]:
    try:
        return serialize(_default_client(authorization).fetch_service_configuration(resource_id=resource_id, service_id=service_id, timezone=timezone))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/start-intervals")
def anny_start_intervals(
    resource_id: str,
    service_id: str,
    date: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> list[object]:
    try:
        return serialize(_default_client(authorization).fetch_start_intervals(resource_id=resource_id, service_id=service_id, date=date, timezone=timezone))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/end-intervals")
def anny_end_intervals(
    resource_id: str,
    service_id: str,
    date_time: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> list[object]:
    try:
        return serialize(_default_client(authorization).fetch_end_intervals(resource_id=resource_id, service_id=service_id, date_time=date_time, timezone=timezone))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/start-dates")
def anny_start_dates(
    resource_id: str,
    service_id: str,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> list[object]:
    try:
        return serialize(
            _default_client(authorization).fetch_start_dates(
                resource_id=resource_id,
                service_id=service_id,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/availability-periods")
def anny_availability_periods(
    resource_id: str,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> list[object]:
    try:
        return serialize(_default_client(authorization).fetch_availability_periods(resource_id=resource_id, start_date=start_date, end_date=end_date, timezone=timezone))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.get("/api/anny/resources/{resource_id}/calendar")
def anny_calendar(
    resource_id: str,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Berlin",
    authorization: str | None = Header(None),
) -> list[object]:
    try:
        return serialize(_default_client(authorization).fetch_calendar_events(resource_id=resource_id, start_date=start_date, end_date=end_date, timezone=timezone))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error


@router.post("/api/anny/bookings/calculate")
def anny_booking_quote(request: AnnyQuoteRequest, authorization: str | None = Header(None)) -> dict[str, object]:
    try:
        return serialize(
            _default_client(authorization).calculate_booking_quote(
                resource_id=request.resource_id,
                service_id=request.service_id,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_anny_error(error) from error

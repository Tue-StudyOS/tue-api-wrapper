from __future__ import annotations

from fastapi import APIRouter, Query

from .advising_discovery import AdvisingDiscovery
from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_common import serialize

router = APIRouter()
discovery = AdvisingDiscovery()


@router.get('/api/people/advising/discover')
def discover_advising() -> dict[str, object]:
    try:
        return serialize(discovery.discover())
    except AlmaError as error:
        raise translate_alma_error(error) from error


@router.post('/api/people/advising/refresh')
def refresh_advising() -> dict[str, object]:
    try:
        return serialize(discovery.refresh())
    except AlmaError as error:
        raise translate_alma_error(error) from error


@router.get('/api/people/advising/search')
def search_advising(query: str = Query(..., min_length=2, max_length=200),
                    limit: int = Query(20, ge=1, le=100)) -> dict[str, object]:
    try:
        return serialize(discovery.search(query, limit=limit))
    except AlmaError as error:
        raise translate_alma_error(error) from error

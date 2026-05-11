from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from .campus_client import CampusClient
from .directory_client import UniversityDirectoryClient
from .directory_models import DirectoryAction, DirectoryForm
from .event_calendar_client import EventCalendarClient
from .fitness_client import FitnessClient
from .hsp_client import HspClient
from .praxisportal_client import PraxisportalClient
from .portal_service import serialize
from .seatfinder_client import SeatfinderClient
from .timms_client import TimmsClient
from .talks_client import TalksClient

router = APIRouter()
timms_client = TimmsClient()
directory_client = UniversityDirectoryClient()
praxisportal_client = PraxisportalClient()
campus_client = CampusClient()
talks_client = TalksClient()
event_calendar_client = EventCalendarClient()
fitness_client = FitnessClient()
hsp_client = HspClient()
seatfinder_client = SeatfinderClient()


def _translate_public_error(error: Exception) -> HTTPException:
    status_code = 502 if isinstance(error, requests.RequestException) else 400
    return HTTPException(status_code=status_code, detail=str(error))


class DirectoryActionRequest(BaseModel):
    query: str
    form: DirectoryForm
    action: DirectoryAction


@router.get("/api/timms/search")
def timms_search(query: str, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)) -> dict[str, object]:
    try:
        return serialize(timms_client.search(query, offset=offset, limit=limit))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/timms/search/suggest")
def timms_search_suggest(term: str, limit: int = Query(8, ge=1, le=20)) -> dict[str, object]:
    try:
        return {"items": timms_client.suggest(term, limit=limit)}
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/timms/items/{item_id}")
def timms_item(item_id: str) -> dict[str, object]:
    try:
        return serialize(timms_client.fetch_item(item_id))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/timms/items/{item_id}/streams")
def timms_streams(item_id: str) -> list[object]:
    try:
        return serialize(timms_client.fetch_streams(item_id))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/timms/items/{item_id}/cite")
def timms_citation(item_id: str, format_name: str = Query(..., alias="format")) -> Response:
    try:
        citation = timms_client.fetch_citation(item_id, format_name=format_name)
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error
    return Response(content=citation.content, media_type=citation.headers.get("content-type", "text/plain"))


@router.get("/api/timms/tree")
def timms_tree(node_id: str = "", node_path: str = "") -> dict[str, object]:
    try:
        return serialize(
            timms_client.fetch_tree(
                node_id=node_id.strip() or None,
                node_path=node_path.strip() or None,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/people/search")
def people_search(query: str = Query(..., min_length=2, max_length=120)) -> dict[str, object]:
    try:
        return serialize(directory_client.search(query))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.post("/api/people/action")
def people_action(request: DirectoryActionRequest) -> dict[str, object]:
    try:
        return serialize(directory_client.submit(query=request.query, form=request.form, action=request.action))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/talks")
def talks(
    scope: str = Query("upcoming", pattern="^(upcoming|previous)$"),
    query: str = "",
    tag_id: list[int] = Query(default=[]),
    include_disabled: bool = False,
    limit: int = Query(24, ge=1, le=100),
) -> dict[str, object]:
    try:
        return serialize(
            talks_client.fetch_talks(
                scope=scope,
                query=query,
                tag_ids=list(tag_id),
                include_disabled=include_disabled,
                limit=limit,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/talks/{talk_id}")
def talk(talk_id: int) -> dict[str, object]:
    try:
        return serialize(talks_client.fetch_talk(talk_id))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/praxisportal/filters")
def praxisportal_filters() -> dict[str, object]:
    try:
        return serialize(praxisportal_client.fetch_filter_options())
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/praxisportal/search")
def praxisportal_search(
    query: str = "",
    project_type_id: list[int] = Query(default=[]),
    industry_id: list[int] = Query(default=[]),
    page: int = Query(0, ge=0),
    per_page: int = Query(20, ge=1, le=50),
    sort: str = Query("newest"),
) -> dict[str, object]:
    try:
        return serialize(
            praxisportal_client.search_projects(
                query=query,
                project_type_ids=tuple(project_type_id),
                industry_ids=tuple(industry_id),
                page=page,
                per_page=per_page,
                sort=sort,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/praxisportal/projects/{project_id}")
def praxisportal_project(project_id: int) -> dict[str, object]:
    try:
        return serialize(praxisportal_client.fetch_project(project_id))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/canteens")
def campus_canteens(menu_date: str | None = Query(None, alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$")) -> list[object]:
    try:
        return serialize(campus_client.fetch_tuebingen_canteens(menu_date=menu_date))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/canteens/{canteen_id}")
def campus_canteen(
    canteen_id: int,
    menu_date: str | None = Query(None, alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$"),
) -> dict[str, object]:
    try:
        return serialize(campus_client.fetch_canteen(canteen_id, menu_date=menu_date))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/buildings")
def campus_buildings() -> dict[str, object]:
    try:
        return serialize(campus_client.fetch_buildings())
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/buildings/detail")
def campus_building_detail(path: str) -> dict[str, object]:
    try:
        return serialize(campus_client.fetch_building_detail(path))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/events")
def campus_events(query: str = Query("", max_length=120), limit: int = Query(24, ge=1, le=100)) -> dict[str, object]:
    try:
        return serialize(event_calendar_client.fetch_events(query=query, limit=limit))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/fitness/kuf")
def campus_kuf_training_occupancy() -> dict[str, object]:
    try:
        return serialize(fitness_client.fetch_kuf_training_occupancy())
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/fitness/courses")
def campus_fitness_courses(
    query: str = Query("", max_length=120),
    area: str | None = Query(None, max_length=80),
    include_unavailable: bool = False,
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, object]:
    try:
        return serialize(
            hsp_client.search_courses(
                query=query,
                area=area,
                include_unavailable=include_unavailable,
                limit=limit,
            )
        )
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/fitness/offers/{title}")
def campus_fitness_offer(title: str) -> dict[str, object]:
    try:
        return serialize(hsp_client.fetch_offer(title))
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error


@router.get("/api/campus/seats")
def campus_seat_availability() -> dict[str, object]:
    try:
        return serialize(seatfinder_client.fetch_availability())
    except Exception as error:  # pragma: no cover - exercised via FastAPI surface
        raise _translate_public_error(error) from error

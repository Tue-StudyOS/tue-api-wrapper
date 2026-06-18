from __future__ import annotations

from fastapi import APIRouter, Query

from .alma_exam_registration_client import (
    inspect_exam_registration_support,
    prepare_exam_registration,
    register_for_exam,
)
from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


def _alma_client():
    return portal_service._alma_client()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


@router.get("/api/alma/exam-registration/support")
def alma_exam_registration_support(
    url: str = "",
    exam_unit_id: str = "",
) -> dict[str, object]:
    try:
        return serialize(inspect_exam_registration_support(_alma_client(), url or None, exam_unit_id=exam_unit_id or None))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/exam-registration/options")
def alma_exam_registration_options(
    url: str = "",
    exam_unit_id: str = "",
) -> dict[str, object]:
    try:
        return serialize(prepare_exam_registration(_alma_client(), url or None, exam_unit_id=exam_unit_id or None))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/alma/exam-registration")
def alma_exam_registration(
    url: str = "",
    exam_unit_id: str = "",
    planelement_id: str = Query(""),
) -> dict[str, object]:
    try:
        result = serialize(
            register_for_exam(
                _alma_client(),
                url or None,
                exam_unit_id=exam_unit_id or None,
                planelement_id=planelement_id or None,
            )
        )
        portal_service.invalidate_portal_cache()
        return result
    except AlmaError as error:
        raise _translate_error(error) from error

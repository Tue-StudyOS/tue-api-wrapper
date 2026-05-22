from __future__ import annotations

from fastapi import APIRouter

from .alma_profile_client import fetch_student_profile
from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


@router.get("/api/alma/profile")
def alma_profile() -> dict[str, object]:
    try:
        return serialize(fetch_student_profile(portal_service._alma_client()))
    except AlmaError as error:
        raise _translate_error(error) from error

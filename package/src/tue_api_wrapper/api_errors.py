from __future__ import annotations

from fastapi import HTTPException

from .config import AlmaError, AlmaServiceUnavailableError

MISSING_UNI_CREDENTIALS_STATUS = 503
ALMA_SERVICE_UNAVAILABLE_STATUS = 503
BAD_REQUEST_STATUS = 400
MISSING_UNI_CREDENTIALS_SIGNAL = "set uni_username and uni_password"


def is_missing_uni_credentials(error: AlmaError | str) -> bool:
    return MISSING_UNI_CREDENTIALS_SIGNAL in str(error).casefold()


def alma_error_status_code(error: AlmaError | str) -> int:
    if isinstance(error, AlmaServiceUnavailableError):
        return ALMA_SERVICE_UNAVAILABLE_STATUS
    if is_missing_uni_credentials(error):
        return MISSING_UNI_CREDENTIALS_STATUS
    return BAD_REQUEST_STATUS


def translate_alma_error(error: AlmaError) -> HTTPException:
    return HTTPException(status_code=alma_error_status_code(error), detail=str(error))

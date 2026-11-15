"""Receipt checks for Moodle assignment submissions."""
from __future__ import annotations

from .config import AlmaParseError


def validate_upload_response(result: object, filename: str, item_id: str) -> None:
    if (not isinstance(result, dict) or result.get('event') or result.get('error')
            or result.get('file') != filename or str(result.get('id')) != item_id):
        raise AlmaParseError('Moodle did not confirm the draft upload; inspect the assignment before retrying')


def classify_receipt(fields, file_verified: bool) -> str:
    if not file_verified:
        return 'unknown'
    statuses = [f.value.strip().casefold() for f in fields
                if f.label.strip().casefold() in {'abgabestatus', 'submission status'}]
    if len(statuses) != 1:
        return 'unknown'
    if statuses[0] in {'zur bewertung abgegeben', 'submitted for grading'}:
        return 'submitted'
    if statuses[0] in {'entwurf (nicht abgegeben)', 'draft (not submitted)'}:
        return 'draft'
    return 'unknown'

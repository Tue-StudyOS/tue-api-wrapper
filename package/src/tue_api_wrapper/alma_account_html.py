from __future__ import annotations

from bs4 import BeautifulSoup

from .alma_account_models import AlmaAccountProfile
from .config import AlmaParseError

CURRENT_ROLE_PREFIX = "CURRENT_ROLE_"
ALL_ROLES_MARKER = "ALL_ROLES"


def parse_account_profile(html: str) -> AlmaAccountProfile:
    soup = BeautifulSoup(html, "html.parser")
    if soup.body is None:
        raise AlmaParseError("Could not find the Alma page body.")

    classes = tuple(str(value) for value in soup.body.get("class", ()))
    current_roles = tuple(
        value.removeprefix(CURRENT_ROLE_PREFIX)
        for value in classes
        if value.startswith(CURRENT_ROLE_PREFIX)
    )
    if len(current_roles) != 1 or not current_roles[0]:
        raise AlmaParseError("Could not determine the current Alma account role.")

    try:
        all_roles_index = classes.index(ALL_ROLES_MARKER)
    except ValueError as exc:
        raise AlmaParseError("Could not determine the available Alma account roles.") from exc

    available_roles = classes[all_roles_index + 1 :]
    if not available_roles or current_roles[0] not in available_roles:
        raise AlmaParseError("Alma returned inconsistent account-role metadata.")
    return AlmaAccountProfile(current_role=current_roles[0], available_roles=available_roles)

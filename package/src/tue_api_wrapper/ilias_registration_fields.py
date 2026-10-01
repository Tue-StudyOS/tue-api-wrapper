from __future__ import annotations

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .ilias_actions_models import IliasRegistrationField, IliasRegistrationOption


def registration_fields(html: str) -> tuple[IliasRegistrationField, ...]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", action=lambda value: bool(value and "ilCourseRegistrationGUI" in value))
    if form is None:
        return ()
    fields = []
    for control in form.find_all(["input", "select", "textarea"]):
        name = control.get("name", "")
        if not name.startswith("cdf_"):
            continue
        label = form.find("label", attrs={"for": control.get("id")}) if control.get("id") else None
        options = tuple(
            IliasRegistrationOption(option.get("value", ""), option.get_text(" ", strip=True))
            for option in control.find_all("option") if option.get("value", "")
        )
        fields.append(IliasRegistrationField(
            name=name,
            label=label.get_text(" ", strip=True) if label else name,
            options=options,
        ))
    return tuple(fields)


def validate_registration_values(html: str, values: dict[str, str]) -> None:
    fields = registration_fields(html)
    names = {field.name for field in fields}
    if set(values) - names:
        raise AlmaParseError("Unknown ILIAS course-registration fields.")
    for field in fields:
        value = values.get(field.name, "").strip()
        if not value:
            raise AlmaParseError(f"ILIAS course registration requires {field.label}.")
        if field.options and value not in {option.value for option in field.options}:
            raise AlmaParseError(f"Invalid selection for {field.label}.")

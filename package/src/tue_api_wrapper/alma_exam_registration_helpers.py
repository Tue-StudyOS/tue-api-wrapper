from __future__ import annotations

import re
from urllib.parse import unquote

from bs4 import BeautifulSoup
from bs4.element import Tag


def find_detail_form(soup: BeautifulSoup) -> Tag | None:
    return soup.find("form", id="detailViewData") or soup.find("form", attrs={"name": "detailViewData"})


def find_enroll_form(soup: BeautifulSoup) -> Tag | None:
    return soup.find("form", id="enrollForm") or soup.find("form", attrs={"name": "enrollForm"})


def extract_jsf_fields(onclick: str) -> dict[str, str]:
    return {unquote(key): unquote(value) for key, value in re.findall(r"""['"]([^'"]+)['"]\s*:\s*['"]([^'"]*)['"]""", onclick)}


def first_target(fields: dict[str, str], suffix: str) -> str | None:
    suffix = suffix.casefold()
    return next((key for key in fields if key.casefold().endswith(suffix)), None)


def option_label(control: Tag, index: int) -> str:
    row = control.find_parent("tr")
    text = clean_text((row or control).get_text(" ", strip=True))
    return text or f"Exam registration path {index + 1}"


def control_identity(control: Tag) -> str:
    return " ".join(
        (
            control.get("name", ""),
            control.get("id", ""),
            control.get("value", ""),
            control.get("title", ""),
            control.get("aria-label", ""),
            control.get_text(" ", strip=True),
            control.get("onclick", ""),
        )
    ).casefold()


def clean_text(value: str) -> str:
    return " ".join(value.split())

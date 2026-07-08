from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .config import AlmaServiceUnavailableError

MAX_NOTICE_LENGTH = 180


def raise_for_alma_unavailable_page(html: str) -> None:
    message = alma_unavailable_message(html)
    if message is not None:
        raise AlmaServiceUnavailableError(message)


def alma_unavailable_message(html: str) -> str | None:
    text = _page_text(html)
    if not text:
        return None

    folded = text.casefold()
    if "wartung" in folded:
        notice = _extract_notice(text, "Wartung")
        return _format_notice("Alma is currently unavailable for maintenance", notice)
    if "maintenance" in folded:
        notice = _extract_notice(text, "maintenance")
        return _format_notice("Alma is currently unavailable for maintenance", notice)
    return None


def _page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


def _extract_notice(text: str, keyword: str) -> str | None:
    match = re.search(
        rf"{re.escape(keyword)}.{{0,{MAX_NOTICE_LENGTH}}}",
        text,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None

    notice = match.group(0).strip()
    sentence = re.split(r"(?<=[.!?])\s+", notice, maxsplit=1)[0]
    time_match = re.search(r"^(.+?\bUhr\b)", sentence, flags=re.IGNORECASE)
    if time_match is not None:
        sentence = time_match.group(1)
    return sentence.rstrip(" .") or None


def _format_notice(prefix: str, notice: str | None) -> str:
    if notice:
        return f"{prefix}: {notice}."
    return f"{prefix}."

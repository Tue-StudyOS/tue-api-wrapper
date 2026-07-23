from __future__ import annotations

from pathlib import PurePosixPath
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .ppi_models import (
    PpiBorrowedLecture,
    PpiBorrowedLecturesPage,
    PpiLecture,
    PpiLectureCatalog,
)

TOKEN_RE = re.compile(r"(?:Anzahl\s+Tokens|Number\s+of\s+Tokens)\s*:\s*(\d+)", re.IGNORECASE)


def parse_lecture_catalog(html: str, source_url: str) -> PpiLectureCatalog:
    soup = BeautifulSoup(html, "html.parser")
    tokens = _token_count(soup)
    lectures: list[PpiLecture] = []
    for cells in _data_rows(soup):
        if len(cells) < 3:
            continue
        title = _text(cells[0])
        protocol_count = _int(_text(cells[1]))
        action = cells[2]
        lecture_id = _query_id(action, "borrow", source_url)
        image_names = _image_names(action)
        borrowed = "protocolCheckmark.png" in image_names
        unavailable = "protocolNotAvailable.png" in image_names or protocol_count <= 0
        lectures.append(
            PpiLecture(
                id=lecture_id,
                title=title,
                protocol_count=protocol_count,
                borrowed=borrowed,
                can_borrow=lecture_id is not None and not borrowed and not unavailable and tokens > 0,
            )
        )
    return PpiLectureCatalog(tokens=tokens, source_url=source_url, lectures=lectures)


def parse_borrowed_lectures(html: str, source_url: str) -> PpiBorrowedLecturesPage:
    soup = BeautifulSoup(html, "html.parser")
    lectures: list[PpiBorrowedLecture] = []
    for cells in _data_rows(soup):
        if len(cells) < 3:
            continue
        lecture_id = _query_id(cells[2], "lecture", source_url)
        if lecture_id is None and len(cells) > 3:
            lecture_id = _query_id(cells[3], "report", source_url)
        lectures.append(
            PpiBorrowedLecture(
                id=lecture_id,
                title=_text(cells[0]),
                borrowed_until=_text(cells[1]),
                download_available=lecture_id is not None and "protocolDownload.png" in _image_names(cells[2]),
            )
        )
    return PpiBorrowedLecturesPage(
        tokens=_token_count(soup),
        source_url=source_url,
        lectures=lectures,
    )


def _token_count(soup: BeautifulSoup) -> int:
    match = TOKEN_RE.search(soup.get_text(" ", strip=True))
    if match is None:
        raise ValueError("PPI page did not expose the account token count.")
    return int(match.group(1))


def _data_rows(soup: BeautifulSoup) -> list[list[Tag]]:
    table = soup.select_one("table#table")
    if table is None:
        raise ValueError("PPI page did not contain the expected lecture table.")
    return [row.find_all("td", recursive=False) for row in table.find_all("tr") if row.find("td")]


def _query_id(cell: Tag, key: str, source_url: str) -> int | None:
    for anchor in cell.find_all("a", href=True):
        query = parse_qs(urlparse(urljoin(source_url, anchor["href"])).query)
        value = query.get(key, [None])[0]
        if value is not None and str(value).isdigit():
            return int(value)
    return None


def _image_names(cell: Tag) -> set[str]:
    return {
        PurePosixPath(urlparse(image["src"]).path).name
        for image in cell.find_all("img", src=True)
    }


def _text(node: Tag) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"PPI returned an invalid protocol count: {value!r}") from error

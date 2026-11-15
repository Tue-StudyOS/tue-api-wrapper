"""Search the Moodle catalogue visible to the authenticated account."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .moodle_models import MoodleCourseSummary


@dataclass(frozen=True)
class MoodleCourseSearchPage:
    source_url: str
    query: str
    page: int
    per_page: int
    items: tuple[MoodleCourseSummary, ...]
    next_page: int | None


def search_moodle_courses(client, query: str, *, page: int = 0, per_page: int = 20) -> MoodleCourseSearchPage:
    response = _request(client, query, page, per_page)
    response.raise_for_status()
    if not 200 <= response.status_code < 300:
        raise AlmaParseError("Moodle course search returned a redirect")
    parsed = urlparse(response.url)
    if parsed.netloc != urlparse(client.base_url).netloc or not parsed.path.endswith("/course/search.php"):
        raise AlmaParseError("Moodle course search redirected away from the search page")
    return _parse_search_page(response.text, response.url, query.strip(), page, per_page)


def _request(client, query: str, page: int, per_page: int):
    if not query.strip() or page < 0 or not 1 <= per_page <= 100:
        raise ValueError("A query, nonnegative page and page size between 1 and 100 are required")
    return client.session.get(f"{client.base_url}/course/search.php",
                              params={"search": query.strip(), "page": page, "perpage": per_page},
                              timeout=client.timeout_seconds, allow_redirects=False)


def raw_moodle_course_search(client, query: str, *, page: int = 0, per_page: int = 20) -> dict:
    response = _request(client, query, page, per_page)
    return {"service": "moodle", "status_code": response.status_code, "request_url": response.url,
            "content_type": response.headers.get("Content-Type"), "location": response.headers.get("Location"),
            "body": response.text}


def _parse_search_page(html: str, url: str, query: str, page: int, per_page: int) -> MoodleCourseSearchPage:
    parsed = urlparse(url)
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".course-search-result")
    if not container:
        headings = " ".join(node.get_text(" ", strip=True) for node in soup.select("h1, h2, h3")).casefold()
        if "no courses were found with the words" in headings:
            return MoodleCourseSearchPage(url, query, page, per_page, (), None)
        raise AlmaParseError("Moodle did not return a recognized course search results container")
    items = []
    for box in container.select(".coursebox"):
        link = box.select_one('.coursename a[href], a[href*="/course/view.php?id="]')
        if not link or not link.get_text(" ", strip=True):
            raise AlmaParseError("Moodle course search returned a course without a title link")
        href = urljoin(url, link["href"])
        ident = parse_qs(urlparse(href).query).get("id", [None])[0]
        if not ident or not ident.isdigit():
            raise AlmaParseError("Moodle course search returned a course without a numeric ID")
        summary = box.select_one(".summary")
        teachers = tuple(node.get_text(" ", strip=True) for node in box.select(".teachers li"))
        items.append(MoodleCourseSummary(int(ident), link.get_text(" ", strip=True), None, None,
                                         None, None, href, None,
                                         summary.get_text(" ", strip=True) if summary else None, teachers))
    if not items:
        raise AlmaParseError("Moodle search results container contains no recognizable courses")
    next_page = None
    for link in soup.select('a[href*="page="]'):
        target = urlparse(urljoin(url, link["href"]))
        params = parse_qs(target.query)
        number = params.get("page", [""])[0]
        if target.netloc == parsed.netloc and target.path == parsed.path and number.isdigit() and int(number) == page + 1:
            next_page = page + 1
            break
    return MoodleCourseSearchPage(url, query, page, per_page, tuple(items), next_page)

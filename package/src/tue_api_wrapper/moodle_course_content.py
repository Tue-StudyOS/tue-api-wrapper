"""Read the content visible on a Moodle course page without following links."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


@dataclass(frozen=True)
class MoodleContentLink:
    service: str
    label: str
    url: str
    section_id: str | None
    activity_id: str | None


@dataclass(frozen=True)
class MoodleContentActivity:
    id: str | None
    kind: str | None
    title: str | None
    url: str | None
    text: str


@dataclass(frozen=True)
class MoodleContentSection:
    id: str | None
    title: str
    description: str
    activities: tuple[MoodleContentActivity, ...]


@dataclass(frozen=True)
class MoodleCourseContent:
    course_id: int
    source_url: str
    coverage: str
    sections: tuple[MoodleContentSection, ...]
    cross_system_links: tuple[MoodleContentLink, ...]


def fetch_course_content(client, course_id: int) -> MoodleCourseContent:
    if isinstance(course_id, bool) or not isinstance(course_id, int) or course_id < 1:
        raise ValueError("Moodle course ID must be a positive integer")
    html, url = client._get_authenticated_page(f"{client.base_url}/course/view.php?id={course_id}")
    target = urlparse(url)
    if (target.netloc != urlparse(client.base_url).netloc or target.path != "/course/view.php"
            or parse_qs(target.query).get("id") != [str(course_id)]):
        raise AlmaParseError("Moodle did not return the requested course page; access may be restricted")
    return parse_course_content(html, url, course_id)


def parse_course_content(html: str, page_url: str, course_id: int) -> MoodleCourseContent:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".course-content")
    sections = container.select("li.course-section") if container else []
    if not sections:
        raise AlmaParseError("Moodle did not return recognizable course sections")
    result, links = [], []
    for section in sections:
        heading = section.select_one(".sectionname")
        if heading is None:
            raise AlmaParseError("Moodle returned a course section without a recognizable title")
        section_id = section.get("id")
        activities = []
        for activity in section.select("li.activity"):
            kind = next((c.removeprefix("modtype_") for c in activity.get("class", []) if c.startswith("modtype_")), None)
            title_node = activity.select_one(".activityname a[href]")
            activities.append(MoodleContentActivity(
                activity.get("id"), kind, title_node.get_text(" ", strip=True) if title_node else None,
                urljoin(page_url, title_node["href"]) if title_node else None,
                activity.get_text(" ", strip=True),
            ))
        for link in section.select("a[href]"):
            url = urljoin(page_url, link["href"])
            parsed = urlparse(url)
            service = {"alma.uni-tuebingen.de": "alma", "ovidius.uni-tuebingen.de": "ilias"}.get(parsed.hostname)
            if service and parsed.scheme in {"http", "https"}:
                activity = link.find_parent("li", class_="activity")
                links.append(MoodleContentLink(service, link.get_text(" ", strip=True), url, section_id,
                                               activity.get("id") if activity else None))
        summary = section.select_one(".summary")
        result.append(MoodleContentSection(section_id, heading.get_text(" ", strip=True),
                                           summary.get_text(" ", strip=True) if summary else "", tuple(activities)))
    return MoodleCourseContent(course_id, page_url, "visible_course_page", tuple(result), tuple(links))

"""Read one Moodle assignment page and preserve its displayed status fields."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


@dataclass(frozen=True)
class AssignmentLink:
    label: str
    url: str


@dataclass(frozen=True)
class AssignmentField:
    label: str
    value: str
    links: tuple[AssignmentLink, ...]


@dataclass(frozen=True)
class MoodleAssignment:
    assignment_id: int
    source_url: str
    title: str
    instructions: str
    instruction_links: tuple[AssignmentLink, ...]
    submission: tuple[AssignmentField, ...]
    feedback: tuple[AssignmentField, ...]
    available_actions: tuple[str, ...]


def fetch_assignment(client, assignment_id: int) -> MoodleAssignment:
    if isinstance(assignment_id, bool) or not isinstance(assignment_id, int) or assignment_id < 1:
        raise ValueError('Moodle assignment activity ID must be a positive integer')
    html, url = client._get_authenticated_page(f'{client.base_url}/mod/assign/view.php?id={assignment_id}')
    target = urlparse(url)
    if (target.netloc != urlparse(client.base_url).netloc or target.path != '/mod/assign/view.php'
            or parse_qs(target.query).get('id') != [str(assignment_id)]):
        raise AlmaParseError('Moodle did not return the requested assignment; access may be restricted')
    return parse_assignment(html, url, assignment_id)


def _links(node, url: str) -> tuple[AssignmentLink, ...]:
    return tuple(AssignmentLink(a.get_text(' ', strip=True), urljoin(url, a['href']))
                 for a in node.select('a[href]') if urlparse(urljoin(url, a['href'])).scheme in {'http', 'https'})


def _fields(container, url: str) -> tuple[AssignmentField, ...]:
    if container is None:
        return ()
    rows = []
    for row in container.select('tr'):
        label, value = row.find('th', recursive=False), row.find('td', recursive=False)
        if label and value:
            rows.append(AssignmentField(label.get_text(' ', strip=True), value.get_text(' ', strip=True), _links(value, url)))
    return tuple(rows)


def parse_assignment(html: str, page_url: str, assignment_id: int) -> MoodleAssignment:
    soup = BeautifulSoup(html, 'html.parser')
    status = soup.select_one('.submissionstatustable')
    title = soup.select_one('#page-header h1, #region-main h1')
    if not status or not title or not _fields(status, page_url):
        raise AlmaParseError('Moodle did not return a recognizable assignment status page')
    intro = soup.select_one('#intro.activity-description, #intro')
    feedback = soup.select_one('.feedback, .feedbacktable')
    actions = []
    for form in soup.select('#region-main form'):
        if form.get('method', 'get').lower() != 'get':
            continue
        action = form.select_one('input[name="action"]')
        target = urlparse(urljoin(page_url, form.get('action', '')))
        if (action and action.get('value') in {'editsubmission', 'submit'}
                and target.netloc == urlparse(page_url).netloc and target.path == '/mod/assign/view.php'):
            actions.append(action['value'])
    return MoodleAssignment(assignment_id, page_url, title.get_text(' ', strip=True),
                            intro.get_text(' ', strip=True) if intro else '', _links(intro, page_url) if intro else (),
                            _fields(status, page_url), _fields(feedback, page_url), tuple(actions))

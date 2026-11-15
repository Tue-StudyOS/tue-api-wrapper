"""Read Moodle quiz overview without starting an attempt."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaParseError


@dataclass(frozen=True)
class MoodleQuiz:
    quiz_id: int
    source_url: str
    title: str
    instructions: str
    information: str
    attempt_summary: tuple[tuple[str, ...], ...]
    can_start: bool


def parse_quiz(html: str, page_url: str, quiz_id: int) -> MoodleQuiz:
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select_one('#page-header h1, #region-main h1')
    container = soup.select_one('#region-main')
    if not title or not container or not (container.select_one('.quizinfo') or container.select_one('.quizattempt')):
        raise AlmaParseError('Moodle did not return a recognizable quiz overview')
    intro = container.select_one('#intro')
    info = container.select_one('.quizinfo')
    rows = tuple(tuple(cell.get_text(' ', strip=True) for cell in row.select('th,td'))
                 for row in container.select('table.quizattemptsummary tr'))
    starts = []
    for form in soup.select('form[method]'):
        action = urlparse(urljoin(page_url, form.get('action', '')))
        cmid = form.select_one('input[name="cmid"]')
        if (form['method'].lower() == 'post' and action.scheme == urlparse(page_url).scheme
                and action.netloc == urlparse(page_url).netloc and action.path == '/mod/quiz/startattempt.php'
                and cmid and cmid.get('value') == str(quiz_id)):
            starts.append(form)
    return MoodleQuiz(quiz_id, page_url, title.get_text(' ', strip=True),
                      intro.get_text(' ', strip=True) if intro else '',
                      info.get_text(' ', strip=True) if info else '', rows, len(starts) == 1)


def fetch_quiz(client, quiz_id: int) -> MoodleQuiz:
    if isinstance(quiz_id, bool) or not isinstance(quiz_id, int) or quiz_id < 1:
        raise ValueError('Moodle quiz ID must be a positive integer')
    html, url = client._get_authenticated_page(f'{client.base_url}/mod/quiz/view.php?id={quiz_id}')
    parsed = urlparse(url)
    if (parsed.netloc != urlparse(client.base_url).netloc or parsed.path != '/mod/quiz/view.php'
            or parse_qs(parsed.query).get('id') != [str(quiz_id)]):
        raise AlmaParseError('Moodle did not return the requested quiz overview')
    return parse_quiz(html, url, quiz_id)

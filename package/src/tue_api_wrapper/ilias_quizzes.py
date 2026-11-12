"""Read-only quiz metadata; never starts or submits a test attempt."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from .config import AlmaParseError
from .ilias_course_client import _course_memberships
from .ilias_feature_client import fetch_ilias_info_page
from .ilias_feature_models import IliasInfoPage
from .models import IliasContentItem

if TYPE_CHECKING:
    from .ilias_client import IliasClient


@dataclass(frozen=True)
class IliasQuiz:
    title: str
    page_url: str
    opens_at: str | None
    closes_at: str | None
    completed_attempts: int | None


@dataclass(frozen=True)
class IliasQuizDeadline:
    course_title: str
    course_url: str
    quiz: IliasQuiz


def quiz_from_info(page: IliasInfoPage) -> IliasQuiz:
    fields = {field.label: field.value for section in page.sections for field in section.fields}
    raw_count = fields.get('Bereits durchgeführte Testdurchläufe')
    if raw_count == 'keine':
        raw_count = '0'
    if raw_count is not None and not re.fullmatch(r'\d+', raw_count):
        raise AlmaParseError('Could not parse ILIAS completed quiz attempt count.')
    return IliasQuiz(
        title=page.title, page_url=page.page_url,
        opens_at=fields.get('Start'), closes_at=fields.get('Ende'),
        completed_attempts=int(raw_count) if raw_count is not None else None,
    )


def is_quiz_item(item: IliasContentItem) -> bool:
    if (item.kind or '').strip().casefold() in {'test', 'quiz'}:
        return True
    parsed = urlparse(item.url)
    query = {k.casefold(): v[-1].casefold() for k, v in parse_qs(parsed.query).items()}
    return '/goto.php/tst/' in parsed.path.casefold() or query.get('cmdclass') in {
        'ilobjtestgui', 'ilias\\test\\presentation\\testscreenGUI'.casefold(),
    }


def fetch_quiz(client: IliasClient, target: str) -> IliasQuiz:
    # Resolve only the object ID, not an attempt/player URL or arbitrary host.
    parsed = urlparse(target)
    if parsed.netloc and parsed.netloc != 'ovidius.uni-tuebingen.de':
        raise AlmaParseError('Quiz targets must belong to the university ILIAS host.')
    refs = parse_qs(parsed.query).get('ref_id')
    match = re.search(r'(\d+)/?$', parsed.path)
    ref_id = refs[-1] if refs else match.group(1) if match else None
    if not ref_id or not ref_id.isdigit():
        raise AlmaParseError('Quiz target must expose a numeric ref_id.')
    return quiz_from_info(fetch_ilias_info_page(client, target=ref_id))


def fetch_course_quizzes(client: IliasClient, target: str) -> tuple[IliasQuiz, ...]:
    page = client.fetch_content_page(target)
    targets = dict.fromkeys(item.url for section in page.sections for item in section.items if is_quiz_item(item))
    return tuple(fetch_quiz(client, url) for url in targets)


def fetch_quiz_deadlines(client: IliasClient, *, course_limit: int = 20, quiz_limit: int = 50) -> tuple[IliasQuizDeadline, ...]:
    deadlines: list[IliasQuizDeadline] = []
    for course in _course_memberships(client.fetch_membership_overview())[:max(1, course_limit)]:
        for quiz in fetch_course_quizzes(client, course.url):
            deadlines.append(IliasQuizDeadline(course.title, course.url, quiz))
            if len(deadlines) >= max(1, quiz_limit):
                return tuple(deadlines)
    return tuple(deadlines)

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_feature_models import IliasInfoField, IliasInfoPage, IliasInfoSection
from tue_api_wrapper.ilias_quizzes import quiz_from_info, is_quiz_item, fetch_quiz
from tue_api_wrapper.models import IliasContentItem


def info(*fields):
    return IliasInfoPage('Quiz 2', 'https://ovidius.uni-tuebingen.de/info', (
        IliasInfoSection('Durchführung', tuple(IliasInfoField(k, v) for k, v in fields)),
    ))


def test_deadline_and_completed_attempts_are_read_from_info():
    quiz = quiz_from_info(info(('Start', '11. Nov 2026, 12:07'),
        ('Ende', '25. Nov 2026, 14:15'), ('Bereits durchgeführte Testdurchläufe', '1')))
    assert quiz.opens_at == '11. Nov 2026, 12:07'
    assert quiz.closes_at == '25. Nov 2026, 14:15'
    assert quiz.completed_attempts == 1


def test_missing_participation_is_unknown_not_zero():
    quiz = quiz_from_info(info(('Ende', '25. Nov 2026, 14:15')))
    assert quiz.completed_attempts is None
    assert quiz.opens_at is None


def test_explicit_no_completed_attempts_is_zero():
    assert quiz_from_info(info(('Bereits durchgeführte Testdurchläufe', 'keine'))).completed_attempts == 0


def test_malformed_attempt_count_is_reported():
    with pytest.raises(AlmaParseError):
        quiz_from_info(info(('Bereits durchgeführte Testdurchläufe', 'changed markup')))


@pytest.mark.parametrize('url,kind,expected', [
    ('https://ovidius.uni-tuebingen.de/goto.php/tst/123', None, True),
    ('https://ovidius.uni-tuebingen.de/ilias.php?cmdClass=ilobjtestgui&ref_id=123', None, True),
    ('https://ovidius.uni-tuebingen.de/test', 'Test', True),
    ('https://ovidius.uni-tuebingen.de/goto.php/exc/123', 'Übung', False),
])
def test_quiz_discovery_does_not_confuse_exercises(url, kind, expected):
    assert is_quiz_item(IliasContentItem('Item', url, kind, ())) is expected


@pytest.mark.parametrize('target', ['https://example.com/tst/123', 'tst/not-an-id'])
def test_invalid_quiz_targets_are_rejected_before_any_request(target):
    with pytest.raises(AlmaParseError):
        fetch_quiz(None, target)

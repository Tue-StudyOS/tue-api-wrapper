import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_quiz_start import parse_start_action, start_ilias_attempt


def test_start_action_must_match_ilias_test_and_never_exposes_query():
    html = '''<h1>Test</h1><button data-action="ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilTestPlayerFixedQuestionSetGUI&amp;cmd=initTest&amp;ref_id=12">Test starten</button>'''
    action = parse_start_action(html, 'https://ovidius.uni-tuebingen.de/ilias.php', 12)
    assert 'cmd=initTest' in action
    with pytest.raises(AlmaParseError):
        parse_start_action(html.replace('ref_id=12', 'ref_id=13'), 'https://ovidius.uni-tuebingen.de/ilias.php', 12)


def test_start_requires_confirmation_before_network():
    with pytest.raises(ValueError):
        start_ilias_attempt(None, 12, 'hash', confirm=False)

import pytest

from tue_api_wrapper.ilias_quiz_answers import prepare_answers, save_answers
from test_ilias_quiz_attempt import HTML, URL


def test_prepare_answers_preserves_hidden_and_requires_known_option():
    review, payload, action = prepare_answers(HTML, URL, 12, {'multiple_choice_result42': ['1']})
    assert ('multiple_choice_result42', '1') in payload
    assert ('cmd[submitSolution]', '1') in payload
    assert 'secret' not in repr(review)
    assert 'rtoken=secret' in action
    with pytest.raises(ValueError):
        prepare_answers(HTML, URL, 12, {'multiple_choice_result42': ['3']})
    with pytest.raises(ValueError):
        prepare_answers(HTML, URL, 12, {'cmd[finishTest]': ['1']})


def test_save_requires_confirmation_without_network():
    with pytest.raises(ValueError):
        save_answers(None, 12, {'multiple_choice_result42': ['1']}, 'review', confirm=False)

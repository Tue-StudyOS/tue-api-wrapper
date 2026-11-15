import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_quiz import parse_quiz


def test_quiz_overview_exposes_instructions_and_start_without_starting():
    html = '''<div id="page-header"><h1>Quiz</h1></div><div id="region-main">
    <div id="intro" class="activity-description">Read instructions</div><div class="quizinfo">Time limit: 1 hour</div>
    <div class="quizattempt"><form method="post" action="/mod/quiz/startattempt.php">
    <input type="hidden" name="cmid" value="42"><input type="hidden" name="sesskey" value="secret"></form></div></div>'''
    result = parse_quiz(html, 'https://moodle.example/mod/quiz/view.php?id=42', 42)
    assert result.instructions == 'Read instructions'
    assert 'Time limit' in result.information
    assert result.can_start is True
    assert 'secret' not in repr(result)


def test_invalid_quiz_page_is_an_error():
    with pytest.raises(AlmaParseError):
        parse_quiz('<h1>login</h1>', 'https://moodle.example/mod/quiz/view.php?id=42', 42)


def test_start_form_rejects_preflight_or_wrong_target():
    from tue_api_wrapper.moodle_quiz_start import parse_start_form
    html = '''<form method="post" action="/mod/quiz/startattempt.php">
      <input type="hidden" name="cmid" value="42"><input type="hidden" name="sesskey" value="secret"></form>'''
    fields = parse_start_form(html, 'https://moodle.example/mod/quiz/view.php?id=42', 42)
    assert fields['cmid'] == '42'
    with pytest.raises(AlmaParseError):
        parse_start_form(html.replace('</form>', '<input name="quizpassword" type="password"></form>'),
                         'https://moodle.example/mod/quiz/view.php?id=42', 42)


def test_start_requires_explicit_confirmation_before_network():
    from tue_api_wrapper.moodle_quiz_start import start_attempt
    with pytest.raises(ValueError):
        start_attempt(None, 42, 'review', confirm=False)


def test_attempt_reader_exposes_questions_and_options_without_session_keys():
    from tue_api_wrapper.moodle_quiz_attempt import parse_attempt
    html = '''<form id="responseform" method="post" action="/mod/quiz/processattempt.php?cmid=42">
    <div class="que multichoice" id="question-1-2"><div class="qtext">Which one?</div>
    <input type="radio" name="q1:2_answer" id="a" value="0"><label for="a">First</label>
    <input type="radio" name="q1:2_answer" id="b" value="1" checked><label for="b">Second</label></div>
    <input type="hidden" name="attempt" value="3"><input type="hidden" name="thispage" value="0">
    <input type="hidden" name="sesskey" value="secret"></form>'''
    result = parse_attempt(html, 'https://moodle.example/mod/quiz/attempt.php?attempt=3&page=0', 3)
    assert result['questions'][0]['text'] == 'Which one?'
    assert result['questions'][0]['fields'][0]['options'][1]['selected']
    assert 'secret' not in repr(result)


def test_answer_form_only_accepts_observed_question_fields():
    from tue_api_wrapper.moodle_quiz_answer import prepare_answer_form
    html = '''<form id="responseform" method="post" action="/mod/quiz/processattempt.php?cmid=42">
    <div class="que multichoice"><div class="qtext">Pick one</div>
    <input type="radio" name="q1:2_answer" value="a"><input type="radio" name="q1:2_answer" value="b"></div>
    <input type="hidden" name="attempt" value="3"><input type="hidden" name="thispage" value="0">
    <input type="hidden" name="timeup" value="0"><input type="hidden" name="sesskey" value="secret"></form>'''
    public, payload, action = prepare_answer_form(html, 'https://moodle.example/mod/quiz/attempt.php?attempt=3&page=0',
                                                   3, {'q1:2_answer': ['b']})
    assert ('q1:2_answer', 'b') in payload
    assert 'secret' not in repr(public)
    with pytest.raises(ValueError):
        prepare_answer_form(html, 'https://moodle.example/mod/quiz/attempt.php?attempt=3&page=0', 3,
                            {'finishattempt': ['1']})
    with pytest.raises(ValueError):
        prepare_answer_form(html, 'https://moodle.example/mod/quiz/attempt.php?attempt=3&page=0', 3,
                            {'q1:2_answer': ['unexpected']})


def test_finish_form_review_exposes_summary_without_session_key():
    from tue_api_wrapper.moodle_quiz_finish import parse_finish_form
    html = '''<div id="region-main"><table class="quizsummaryofattempt"><tr><th>Question</th><td>Answered</td></tr></table>
    <form id="frm-finishattempt" method="post" action="/mod/quiz/processattempt.php">
    <input type="hidden" name="attempt" value="3"><input type="hidden" name="finishattempt" value="1">
    <input type="hidden" name="timeup" value="0"><input type="hidden" name="sesskey" value="secret"></form></div>'''
    review, payload = parse_finish_form(html, 'https://moodle.example/mod/quiz/summary.php?attempt=3', 3)
    assert 'Answered' in review['summary']
    assert payload['finishattempt'] == '1'
    assert 'secret' not in repr(review)

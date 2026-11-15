import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_quiz_attempt import parse_question, resume_action


URL = 'https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&cmdClass=ilTestPlayerFixedQuestionSetGUI&cmd=showQuestion&ref_id=12&sequence=3'
HTML = '''<div id="tst_output"><form id="taForm" method="post" action="ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilTestPlayerFixedQuestionSetGUI&amp;cmd=post&amp;fallbackCmd=submitIntermediateSolution&amp;ref_id=12&amp;sequence=3&amp;rtoken=secret">
<input type="hidden" name="formtimestamp" value="123"><div class="ilc_question_SingleChoice">
<div class="ilc_qtitle_Title">Which answer?</div><input type="radio" name="multiple_choice_result42" value="1" id="a"><label for="a">First</label>
<input type="radio" name="multiple_choice_result42" value="2" id="b" checked><label for="b">Second</label>
</div></form></div>'''


def test_parse_question_exposes_choices_without_session_tokens():
    result = parse_question(HTML, URL, 12)
    assert result['question']['text'] == 'Which answer?'
    assert result['question']['fields'][0]['options'][1]['selected']
    assert 'secret' not in repr(result)


def test_question_resources_include_images_but_not_action_tokens():
    html = HTML.replace('Which answer?', 'Which answer? <img src="/diagram.png" alt="Diagram"><a href="ilias.php?rtoken=secret">hidden</a>')
    resources = parse_question(html, URL, 12)['question']['resources']
    assert resources == [{'kind': 'image', 'url': 'https://ovidius.uni-tuebingen.de/diagram.png', 'label': 'Diagram'}]


def test_resume_only_accepts_existing_attempt_action():
    html = '''<button data-action="ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilTestPlayerFixedQuestionSetGUI&amp;cmd=resumePlayer&amp;ref_id=12">Continue</button>'''
    assert 'resumePlayer' in resume_action(html, URL, 12)
    with pytest.raises(AlmaParseError):
        resume_action(html.replace('resumePlayer', 'initTest'), URL, 12)
    with pytest.raises(AlmaParseError):
        resume_action(html.replace('ref_id=12', 'ref_id=12&amp;cmd[finishTest]=1'), URL, 12)


def test_wrong_question_action_or_unsupported_type_fails_closed():
    with pytest.raises(AlmaParseError):
        parse_question(HTML.replace('submitIntermediateSolution', 'finishTest'), URL, 12)
    with pytest.raises(AlmaParseError):
        parse_question(HTML.replace('ilc_question_SingleChoice', 'ilc_question_FormulaQuestion'), URL, 12)


def test_locked_question_can_be_read_without_exposing_editable_fields():
    html = HTML.replace('class="ilc_question_SingleChoice"', 'class="ilc_question_SingleChoice readonly"')
    html = html.replace('type="radio"', 'type="radio" disabled')
    result = parse_question(html, URL, 12)
    assert result['question']['editable'] is False
    assert result['question']['fields'] == []

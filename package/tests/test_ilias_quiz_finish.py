import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_quiz_finish import finish_link, parse_finish_modal, finish_attempt


URL = 'https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&cmdClass=ilTestPlayerFixedQuestionSetGUI&cmd=showQuestion&ref_id=12&sequence=3'
FINISH = 'ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilTestPlayerFixedQuestionSetGUI&amp;cmd=finishTest&amp;ref_id=12&amp;finalization_confirmed=confirmed'


def test_finish_review_requires_server_confirmation_modal():
    html = f'''<dialog class="c-modal c-modal--interruptive"><form method="post" action="{FINISH}">
      <h1 class="modal-title">Finish test</h1><div class="c-modal--interruptive__message">Are you sure?</div>
      <input type="submit" value="Finish"></form></dialog>'''
    public, action = parse_finish_modal(html, URL, 12)
    assert public['message'] == 'Are you sure?'
    assert 'finalization_confirmed=confirmed' in action
    with pytest.raises(AlmaParseError):
        parse_finish_modal(html.replace('finalization_confirmed=confirmed', 'finalization_confirmed=no'), URL, 12)


def test_finish_link_is_extracted_from_navigation_without_final_confirmation():
    action = URL.replace('showQuestion', 'finishTest')
    html = f'<script>il.TestPlayerQuestionEditControl.checkNavigation(\'{action}\', \'show\', e);</script>'
    assert finish_link(html, URL, 12) == action
    with pytest.raises(AlmaParseError):
        finish_link(html.replace('finishTest', 'initTest'), URL, 12)


def test_finish_requires_confirmation_before_network():
    with pytest.raises(ValueError):
        finish_attempt(None, 12, 'hash', confirm=False)

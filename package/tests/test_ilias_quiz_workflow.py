from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from tue_api_wrapper.ilias_quiz_attempt import fetch_question
from tue_api_wrapper.ilias_quiz_answers import review_answers, save_answers
from tue_api_wrapper.ilias_quiz_finish import review_finish, finish_attempt
from test_ilias_quiz_attempt import HTML, URL


class Response:
    def __init__(self, url, text='', status=200, location=None):
        self.url, self.text, self.status_code = url, text, status
        self.headers = {'Location': location} if location else {}
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP error')


class FakeIlias:
    timeout_seconds = 5
    def __init__(self):
        self.session = self
        self.answer = '2'
        self.completed = 0
        self.posts = []
    def get(self, url, **kwargs):
        p, q = urlparse(url), parse_qs(urlparse(url).query)
        if p.path.startswith('/goto.php/'):
            html = '''<button data-action="/ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilTestPlayerFixedQuestionSetGUI&amp;cmd=resumePlayer&amp;ref_id=12">Continue</button>'''
            return Response(url, html)
        cmd = q.get('cmd', [''])[0]
        if cmd == 'resumePlayer':
            return Response(url, status=303, location=URL)
        if cmd == 'showQuestion':
            html = HTML.replace('value="2" id="b" checked', f'value="2" id="b" {"checked" if self.answer == "2" else ""}')
            html = html.replace('value="1" id="a"', f'value="1" id="a" {"checked" if self.answer == "1" else ""}')
            finish = URL.replace('showQuestion', 'finishTest')
            html += f'<script>il.TestPlayerQuestionEditControl.checkNavigation(\'{finish}\', \'show\', e);</script>'
            return Response(url, html)
        if cmd == 'finishTest' and 'finalization_confirmed' not in q:
            action = URL.replace('showQuestion', 'finishTest') + '&finalization_confirmed=confirmed'
            html = f'''<dialog class="c-modal c-modal--interruptive"><form method="post" action="{action}">
            <h1 class="modal-title">Finish</h1><div class="c-modal--interruptive__message">Finish now?</div></form></dialog>'''
            return Response(url, html)
        raise AssertionError('unexpected GET command')
    def post(self, url, data=None, **kwargs):
        self.posts.append(url)
        query = parse_qs(urlparse(url).query)
        if query.get('cmd') == ['post']:
            self.answer = dict(data)['multiple_choice_result42']
        elif query.get('finalization_confirmed') == ['confirmed']:
            self.completed += 1
        else:
            raise AssertionError('unexpected POST command')
        return Response(url, status=303)


def test_read_save_finish_using_only_controlled_session(monkeypatch):
    import tue_api_wrapper.ilias_quiz_finish as finish
    client = FakeIlias()
    monkeypatch.setattr(finish, 'fetch_quiz', lambda *args: SimpleNamespace(completed_attempts=client.completed))
    assert fetch_question(client, 12)['question']['text'] == 'Which answer?'
    answers = {'multiple_choice_result42': ['1']}
    review = review_answers(client, 12, answers)
    with pytest.raises(ValueError):
        save_answers(client, 12, answers, review['review_sha256'], confirm=False)
    assert not client.posts
    saved = save_answers(client, 12, answers, review['review_sha256'], confirm=True)
    assert saved['outcome'] == 'unverified' and saved['values_match'] is True
    review = review_finish(client, 12)
    with pytest.raises(ValueError):
        finish_attempt(client, 12, review['review_sha256'], confirm=False)
    assert len(client.posts) == 1
    result = finish_attempt(client, 12, review['review_sha256'], confirm=True)
    assert result['outcome'] == 'finished' and client.completed == 1


def test_no_resume_action_never_starts_a_test():
    from tue_api_wrapper.config import AlmaParseError
    class NoResume(FakeIlias):
        def get(self, url, **kwargs):
            return Response(url, '<button data-action="ilias.php?cmd=initTest">Start</button>')
    client = NoResume()
    with pytest.raises(AlmaParseError):
        fetch_question(client, 12)
    assert not client.posts


def test_cli_and_mcp_expose_question_and_confirmed_writes(monkeypatch, capsys):
    import json
    from tue_api_wrapper import moodle_quiz_cli, mcp_quiz_write
    transport = FakeIlias()
    client = SimpleNamespace(ilias=SimpleNamespace(client=transport), close=lambda: None)
    monkeypatch.setattr(moodle_quiz_cli, 'make_client', lambda _: (client, 'student'))
    monkeypatch.setattr(mcp_quiz_write, 'make_client', lambda _: (client, 'student'))
    assert moodle_quiz_cli.main(['read', '--service', 'ilias', '--target', '12']) == 0
    assert json.loads(capsys.readouterr().out)['question']['text'] == 'Which answer?'
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    mcp_quiz_write.register_quiz_write_tools(Server(), None)
    answer = {'multiple_choice_result42': ['1']}
    review = tools['ilias_quiz_review_answers'](12, answer)
    with pytest.raises(ValueError):
        tools['ilias_quiz_save_answers'](12, answer, review['review_sha256'])
    assert not transport.posts
    result = tools['ilias_quiz_save_answers'](12, answer, review['review_sha256'], confirm=True)
    assert result['outcome'] == 'unverified' and result['values_match'] is True

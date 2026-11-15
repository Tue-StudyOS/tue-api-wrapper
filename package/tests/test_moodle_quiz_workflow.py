from urllib.parse import parse_qs, urlparse

import pytest

from tue_api_wrapper.moodle_quiz_start import review_start, start_attempt
from tue_api_wrapper.moodle_quiz_answer import review_answers, save_answers
from tue_api_wrapper.moodle_quiz_finish import review_finish, finish_attempt


class Response:
    def __init__(self, url, text='', status=200, location=None):
        self.url, self.text, self.status_code = url, text, status
        self.headers = {'Location': location} if location else {}
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP error')


class FakeQuiz:
    base_url = 'https://moodle.example'
    timeout_seconds = 5
    def __init__(self):
        self.session = self
        self.answer = None
        self.finished = False
        self.posts = []
    def get(self, url, **kwargs):
        p = urlparse(url)
        if p.path.endswith('/view.php'):
            html = '''<div id="page-header"><h1>Quiz</h1></div><div id="region-main"><div class="quizinfo">60 minutes</div>
              <div class="quizattempt"><form method="post" action="/mod/quiz/startattempt.php">
              <input type="hidden" name="cmid" value="42"><input type="hidden" name="sesskey" value="secret"></form></div></div>'''
        elif p.path.endswith('/attempt.php'):
            checked = 'checked' if self.answer == 'b' else ''
            html = f'''<form id="responseform" method="post" action="/mod/quiz/processattempt.php?cmid=42">
            <div class="que multichoice"><div class="qtext">Pick one</div>
            <input type="radio" name="q1:2_answer" value="a"><input type="radio" name="q1:2_answer" value="b" {checked}></div>
            <input type="hidden" name="attempt" value="3"><input type="hidden" name="thispage" value="0">
            <input type="hidden" name="slots" value="2"><input type="hidden" name="timeup" value="0">
            <input type="hidden" name="sesskey" value="secret"></form>'''
        elif p.path.endswith('/summary.php'):
            html = '''<div id="region-main"><table><tr><th>Question</th><td>Answered</td></tr></table>
            <form id="frm-finishattempt" method="post" action="/mod/quiz/processattempt.php">
            <input type="hidden" name="attempt" value="3"><input type="hidden" name="finishattempt" value="1">
            <input type="hidden" name="sesskey" value="secret"></form></div>'''
        elif p.path.endswith('/review.php'):
            status = 'Finished' if self.finished else 'In progress'
            html = f'<div id="region-main"><table><tr><th>State</th><td>{status}</td></tr></table></div>'
        else:
            raise AssertionError(p.path)
        return Response(url, html)
    def post(self, url, data, **kwargs):
        self.posts.append(url)
        if url.endswith('/startattempt.php'):
            return Response(url, status=303, location='/mod/quiz/attempt.php?attempt=3')
        fields = dict(data)
        if fields.get('finishattempt') == '1':
            self.finished = True
        else:
            self.answer = fields.get('q1:2_answer')
        return Response(url, status=303, location='/mod/quiz/attempt.php?attempt=3')


def test_review_start_save_and_finish_against_controlled_session():
    client = FakeQuiz()
    preview = review_start(client, 42)
    with pytest.raises(ValueError):
        start_attempt(client, 42, preview['review_sha256'], confirm=False)
    assert client.posts == []
    assert start_attempt(client, 42, preview['review_sha256'], confirm=True)['attempt_id'] == 3
    answers = {'q1:2_answer': ['b']}
    preview = review_answers(client, 3, 0, answers)
    assert save_answers(client, 3, 0, answers, preview['review_sha256'], confirm=True)['outcome'] == 'saved'
    preview = review_finish(client, 3)
    assert finish_attempt(client, 3, preview['review_sha256'], confirm=True)['outcome'] == 'finished'


def test_quiz_write_tools_are_opt_in():
    from tue_api_wrapper.mcp_server import _enabled_services
    assert 'quiz-write' not in _enabled_services(None)
    assert 'quiz-write' in _enabled_services(['quiz-write'])


def test_quiz_actions_require_confirmation_before_connecting(monkeypatch):
    from tue_api_wrapper import mcp_quiz_write
    monkeypatch.setattr(mcp_quiz_write, 'make_client', lambda _: (_ for _ in ()).throw(AssertionError('must not connect')))
    tools = {}
    class Server:
        def tool(self):
            return lambda fn: tools.setdefault(fn.__name__, fn)
    mcp_quiz_write.register_quiz_write_tools(Server(), None)
    for tool, args in [('moodle_quiz_start', (42, 'hash')), ('ilias_quiz_start', (42, 'hash')),
                       ('moodle_quiz_save_answers', (3, 0, {'q1:2_answer': ['b']}, 'hash')),
                       ('moodle_quiz_finish', (3, 'hash'))]:
        with pytest.raises(ValueError):
            tools[tool](*args)

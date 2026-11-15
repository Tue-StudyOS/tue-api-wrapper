import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.moodle_forums import parse_forum, parse_discussion


FORUM_URL = 'https://moodle.zdv.uni-tuebingen.de/mod/forum/view.php?id=12'
THREAD_URL = 'https://moodle.zdv.uni-tuebingen.de/mod/forum/discuss.php?d=34'


def test_forum_lists_discussions_and_pagination():
    html = '''<div id="page-header"><h1>Questions</h1></div><div id="region-main">
    <table class="discussion-list"><tr class="discussion"><th class="topic"><a href="discuss.php?d=34">Help</a></th>
    <td class="author">Alex</td><td class="replies">2</td></tr></table>
    <a rel="next" href="view.php?id=12&amp;page=1">Next</a></div>'''
    result = parse_forum(html, FORUM_URL, 12)
    assert result.discussions[0].title == 'Help'
    assert result.discussions[0].url == THREAD_URL
    assert result.next_url.endswith('page=1')


def test_discussion_reads_posts_without_combining_nested_replies():
    html = '''<div id="page-header"><h1>Help</h1></div><div id="region-main">
    <article data-region="post" data-post-id="3"><header><h3>First</h3><a href="/user/view.php?id=1">Alex</a><time datetime="2026-11-01">Sunday</time></header>
    <div class="post-content-container"><p>What happened?</p><a href="/pluginfile.php/3/file.pdf">file.pdf</a></div>
    <div data-region="replies-container"><article data-region="post" data-post-id="4"><header><h3>Reply</h3></header>
    <div class="post-content-container">Answer</div></article></div></article></div>'''
    page = parse_discussion(html, THREAD_URL, 34)
    assert len(page.posts) == 2
    assert page.posts[0].body == 'What happened? file.pdf'
    assert page.posts[0].attachments[0].url.endswith('/pluginfile.php/3/file.pdf')
    assert page.posts[1].parent_id == '3'


def test_unrecognized_forum_and_discussion_are_errors():
    with pytest.raises(AlmaParseError):
        parse_forum('<html>login</html>', FORUM_URL, 12)
    with pytest.raises(AlmaParseError):
        parse_discussion('<html>login</html>', THREAD_URL, 34)


def test_forum_post_form_preserves_only_supported_fields():
    from tue_api_wrapper.moodle_forum_write import parse_post_form
    html = '''<form method="post" action="/mod/forum/post.php">
    <input type="hidden" name="forum" value="7"><input type="hidden" name="parent" value="0">
    <input type="hidden" name="sesskey" value="secret"><input type="hidden" name="message[format]" value="1">
    <input name="subject" type="text"><textarea name="message[text]"></textarea>
    <input type="submit" name="submitbutton" value="Post"></form>'''
    form = parse_post_form(html, FORUM_URL, mode='new', target=12)
    assert form['forum'] == '7' and form['sesskey'] == 'secret'
    with pytest.raises(AlmaParseError):
        parse_post_form(html.replace('/mod/forum/post.php', 'https://evil.example/post.php'), FORUM_URL, mode='new', target=12)


def test_posting_requires_confirmation_without_network():
    from tue_api_wrapper.moodle_forum_write import publish_post
    with pytest.raises(ValueError):
        publish_post(None, 'reply', 12, 'subject', 'body', 'hash', confirm=False)


def test_publish_checks_review_and_verifies_post_id_and_content(monkeypatch):
    from types import SimpleNamespace
    from tue_api_wrapper import moodle_forum_write as writer
    fields = {'sesskey': 'secret', 'forum': '7', 'discussion': '34', 'parent': '12',
              'groupid': '0', 'message[format]': '1'}
    monkeypatch.setattr(writer, '_form', lambda *args: dict(fields))
    monkeypatch.setattr(writer, 'fetch_discussion', lambda client, did: SimpleNamespace(
        posts=[SimpleNamespace(id='55', body='Hello world')]))
    class Session:
        calls = 0
        def post(self, url, **kwargs):
            self.calls += 1
            assert kwargs['data']['message[text]'] == '<p>Hello world</p>'
            return SimpleNamespace(status_code=303, headers={'Location': '/mod/forum/discuss.php?d=34#p55'},
                                   raise_for_status=lambda: None)
    session = Session()
    client = SimpleNamespace(session=session, base_url='https://moodle.example', timeout_seconds=5)
    preview = writer.review_post(client, 'reply', 12, 'Subject', 'Hello world')
    with pytest.raises(ValueError):
        writer.publish_post(client, 'reply', 12, 'Subject', 'different', preview['review_sha256'], confirm=True)
    assert session.calls == 0
    result = writer.publish_post(client, 'reply', 12, 'Subject', 'Hello world', preview['review_sha256'], confirm=True)
    assert result['outcome'] == 'confirmed' and result['post_id'] == '55'

import pytest

from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.ilias_forum_threads import parse_thread, validate_thread_url


URL = 'https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&cmdClass=ilObjForumGUI&cmd=viewThread&ref_id=1&thr_pk=2'


def test_thread_parses_posts_and_links_without_following_mark_read():
    html = '''<h1>Discussion</h1><ul id="ilFrmPostList"><li class="ilFrmPostRow ilFrmPost-level-1">
    <div class="ilFrmPostHeader"><span class="small">Alex | Monday</span><div class="ilFrmPostTitle">
    <a href="ilias.php?cmd=markPostRead&amp;pos_pk=3">Subject</a></div></div>
    <div class="ilFrmPostContent">Question <a href="/files/a.pdf">attachment</a></div></li></ul>'''
    page = parse_thread(html, URL)
    assert page.posts[0].id == '3'
    assert page.posts[0].author_and_date == 'Alex | Monday'
    assert page.posts[0].body == 'Question attachment'
    assert page.posts[0].links[0].url.endswith('/files/a.pdf')


@pytest.mark.parametrize('target', ['https://evil.example/ilias.php?cmd=viewThread',
 'https://ovidius.uni-tuebingen.de/ilias.php?cmd=markPostRead&ref_id=1&thr_pk=2'])
def test_thread_target_refuses_other_hosts_and_mutating_commands(target):
    with pytest.raises(AlmaParseError):
        validate_thread_url(target)


def test_post_form_requires_correct_host_and_submit_command():
    from tue_api_wrapper.ilias_forum_write import parse_editor
    html = '''<form method="post" action="ilias.php?cmd=post&amp;fallbackCmd=savePost&amp;ref_id=1&amp;thr_pk=2&amp;pos_pk=3&amp;rtoken=secret">
      <input name="subject" type="text"><textarea name="message"></textarea>
      <input name="alias" type="text" value=""><input name="cmd[savePost]" type="submit" value="Send">
      <input name="draft_id" type="hidden" value="5"></form>'''
    form = parse_editor(html, URL, forum_id='1', mode='reply', thread_id='2', parent_id='3')
    assert form['fields']['draft_id'] == '5'
    assert form['fields']['cmd[savePost]'] == 'Send'
    with pytest.raises(AlmaParseError):
        parse_editor(html.replace('ilias.php?', 'https://evil.example/ilias.php?'), URL, forum_id='1', mode='reply', thread_id='2', parent_id='3')


def test_ilias_publish_requires_post_specific_receipt(monkeypatch):
    from types import SimpleNamespace
    from tue_api_wrapper import ilias_forum_write as writer
    preview = {'review_sha256': 'review', 'alias': '', 'rich_text': False, 'forum_id': '1'}
    monkeypatch.setattr(writer, 'review_ilias_post', lambda *args: preview)
    monkeypatch.setattr(writer, '_editor', lambda *args: ({'action': URL, 'fields': {'alias': ''}, 'rich_text': False}, '1'))
    monkeypatch.setattr(writer, 'fetch_thread', lambda *args: SimpleNamespace(posts=[
        SimpleNamespace(id='7', subject='Subject', body='Body')]))
    class Session:
        def post(self, *args, **kwargs):
            loc = URL + '&pos_pk=7'
            return SimpleNamespace(status_code=303, headers={'Location': loc}, raise_for_status=lambda: None)
    client = SimpleNamespace(session=Session(), timeout_seconds=1)
    result = writer.publish_ilias_post(client, 'reply', URL, 'Subject', 'Body', 'review', confirm=True, parent_id='3')
    assert result['outcome'] == 'confirmed' and result['post_id'] == '7'

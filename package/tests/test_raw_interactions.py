from types import SimpleNamespace

import pytest

from tue_api_wrapper.raw_interactions import raw_interaction


def test_raw_moodle_read_returns_unparsed_body_without_following_redirects():
    calls = []
    class Session:
        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return SimpleNamespace(status_code=200, url=url, text='<unparsed>', headers={'Content-Type': 'text/html'})
    moodle = SimpleNamespace(session=Session(), timeout_seconds=1, base_url='https://moodle.example')
    client = SimpleNamespace(moodle=SimpleNamespace(client=moodle))
    result = raw_interaction(client, 'moodle', 'discussion', '42')
    assert result['body'] == '<unparsed>'
    assert calls[0][1]['allow_redirects'] is False
    assert calls[0][0].endswith('/mod/forum/discuss.php?d=42')


def test_raw_read_rejects_arbitrary_targets():
    with pytest.raises(ValueError):
        raw_interaction(None, 'moodle', 'quiz', 'https://evil.example')

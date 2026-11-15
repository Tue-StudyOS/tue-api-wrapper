from types import SimpleNamespace

import pytest

from tue_api_wrapper.raw_course_response import get_raw_course_response


def test_raw_course_fetch_returns_unparsed_body_and_does_not_follow_redirects():
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200, text="<html>raw page</html>", headers={"Content-Type": "text/html"})
    client = SimpleNamespace(moodle=SimpleNamespace(client=SimpleNamespace(session=SimpleNamespace(get=get), timeout_seconds=10)))
    result = get_raw_course_response(client, "moodle", "123")
    assert result["body"] == "<html>raw page</html>"
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][0] == "https://moodle.zdv.uni-tuebingen.de/course/view.php?id=123"


def test_raw_course_fetch_rejects_non_numeric_target():
    with pytest.raises(ValueError):
        get_raw_course_response(object(), "ilias", "https://evil.example/")

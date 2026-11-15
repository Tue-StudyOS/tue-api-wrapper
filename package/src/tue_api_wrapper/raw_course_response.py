"""Explicit raw reads of fixed course-page endpoints, without parser involvement."""
from __future__ import annotations

from typing import Any


def get_raw_course_response(client: Any, service: str, course_id: str) -> dict[str, Any]:
    if not course_id.isascii() or not course_id.isdigit():
        raise ValueError("Course ID must contain ASCII digits only")
    if service == "moodle":
        source = client.moodle.client
        url = f"https://moodle.zdv.uni-tuebingen.de/course/view.php?id={course_id}"
    elif service == "ilias":
        source = client.ilias.client
        url = f"https://ovidius.uni-tuebingen.de/goto.php/crs/{course_id}"
    else:
        raise ValueError("Raw course reads support moodle and ilias")
    response = source.session.get(url, timeout=source.timeout_seconds, allow_redirects=False)
    return {"service": service, "request_url": url, "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"), "location": response.headers.get("Location"),
            "body": response.text, "redirects_followed": False}

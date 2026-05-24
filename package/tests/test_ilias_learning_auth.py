from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.ilias_client import IliasClient
from tue_api_wrapper.ilias_learning_html import parse_membership_overview, parse_task_overview


AUTHENTICATED_EMPTY_PAGE = """
<html>
  <head><title>ILIAS</title></head>
  <body>
    <ul class="il-mainbar-entries"></ul>
    <a href="logout.php?baseClass=ilstartupgui">Abmelden</a>
  </body>
</html>
"""


class _FakeResponse:
    def __init__(self, *, url: str, text: str) -> None:
        self.url = url
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self.headers: dict[str, str] = {}
        self.response = response
        self.urls: list[str] = []

    def get(self, url: str, **_: object) -> _FakeResponse:
        self.urls.append(url)
        return self.response


class IliasLearningAuthTests(unittest.TestCase):
    def test_empty_authenticated_membership_overview_returns_no_items(self) -> None:
        items = parse_membership_overview(
            AUTHENTICATED_EMPTY_PAGE,
            "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilmembershipoverviewgui",
        )

        self.assertEqual(items, ())

    def test_empty_authenticated_task_overview_returns_no_items(self) -> None:
        items = parse_task_overview(
            AUTHENTICATED_EMPTY_PAGE,
            "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui",
        )

        self.assertEqual(items, ())

    def test_client_uses_root_ovidius_learning_urls(self) -> None:
        response = _FakeResponse(
            url="https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui",
            text=AUTHENTICATED_EMPTY_PAGE,
        )
        session = _FakeSession(response)
        client = IliasClient(session=session)

        self.assertEqual(client.fetch_task_overview(), ())

        response.url = "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilmembershipoverviewgui"
        self.assertEqual(client.fetch_membership_overview(), ())
        self.assertEqual(
            session.urls,
            [
                "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui",
                "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilmembershipoverviewgui",
            ],
        )


if __name__ == "__main__":
    unittest.main()

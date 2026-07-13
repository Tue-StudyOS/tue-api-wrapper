from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_account_client import fetch_account_profile
from tue_api_wrapper.alma_account_html import parse_account_profile
from tue_api_wrapper.client import AlmaClient
from tue_api_wrapper.config import AlmaLoginError, AlmaParseError


class AlmaAccountProfileHtmlTests(unittest.TestCase):
    def test_parses_observed_dozent_account_roles(self) -> None:
        profile = parse_account_profile(
            '<html><body class="loggedin CURRENT_ROLE_dozent ALL_ROLES dozent pruefer"></body></html>'
        )

        self.assertEqual(profile.current_role, "dozent")
        self.assertEqual(profile.available_roles, ("dozent", "pruefer"))

    def test_parses_current_and_available_roles_as_server_strings(self) -> None:
        profile = parse_account_profile(
            '<html><body class="loggedin CURRENT_ROLE_custom-role ALL_ROLES student custom-role"></body></html>'
        )

        self.assertEqual(profile.current_role, "custom-role")
        self.assertEqual(profile.available_roles, ("student", "custom-role"))

    def test_rejects_missing_role_metadata(self) -> None:
        with self.assertRaisesRegex(AlmaParseError, "current Alma account role"):
            parse_account_profile('<html><body class="loggedin"></body></html>')


class AlmaAccountProfileClientTests(unittest.TestCase):
    def test_fetches_profile_from_authenticated_start_page(self) -> None:
        response = _FakeResponse(
            '<html><body class="loggedin CURRENT_ROLE_student ALL_ROLES student"></body></html>'
        )
        session = _FakeSession(response)
        client = AlmaClient(session=session)

        profile = fetch_account_profile(client)

        self.assertEqual(profile.current_role, "student")
        self.assertEqual(profile.available_roles, ("student",))
        self.assertEqual(session.requested_url, client.start_page_url)

    def test_rejects_an_unauthenticated_start_page(self) -> None:
        client = AlmaClient(session=_FakeSession(_FakeResponse('<form id="loginForm"></form>')))

        with self.assertRaisesRegex(AlmaLoginError, "not authenticated"):
            fetch_account_profile(client)


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.requested_url: str | None = None

    def get(self, url: str, *, timeout: int, allow_redirects: bool) -> _FakeResponse:
        self.requested_url = url
        return self.response


if __name__ == "__main__":
    unittest.main()

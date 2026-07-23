from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
import unittest

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import tue_api_wrapper
from tue_api_wrapper.ppi_client import (
    PpiAccessError,
    PpiAuthenticationError,
    PpiClient,
    PpiValidationError,
)
from test_ppi_html import BORROWED_HTML, LECTURES_HTML


LOGIN_HTML = '<html><form><input name="username"><input name="password"></form></html>'
BORROWED_AFTER_HTML = LECTURES_HTML.replace(
    '<a href="?borrow=42"><img src="static/img/protocol.png">Ausleihen</a>',
    '<a href="download.php"><img src="static/img/protocolCheckmark.png">Ausgeliehen</a>',
)
TOKEN_SUCCESS_HTML = "<html><body>Vielen Dank! Wir überprüfen deinen Antrag für mehr Tokens.</body></html>"


class PpiClientTests(unittest.TestCase):
    def test_package_exports_ppi_client(self) -> None:
        self.assertIs(tue_api_wrapper.PpiClient, PpiClient)

    def test_signup_creates_independent_ppi_account(self) -> None:
        session = _FakeSession([
            _FakeResponse(url="https://ppi.example/create.php", text="<html></html>"),
            _FakeResponse(status_code=302, url="https://ppi.example/create.php", headers={"Location": "activate.php"}),
        ])

        result = PpiClient(base_url="https://ppi.example", session=session).signup(
            "ZXABC12",
            "ppi-only-password",
        )

        self.assertEqual(result.username, "zxabc12")
        self.assertEqual(result.activation_email, "zxabc12@student.uni-tuebingen.de")
        post = session.calls[1]
        self.assertEqual(post.method, "POST")
        self.assertEqual(
            post.kwargs["data"],
            {
                "username": "zxabc12",
                "password": "ppi-only-password",
                "password_repeated": "ppi-only-password",
            },
        )

    def test_signup_rejects_non_zdv_username_before_network(self) -> None:
        session = _FakeSession([])

        with self.assertRaises(PpiValidationError):
            PpiClient(base_url="https://ppi.example", session=session).signup("student", "secret")

        self.assertEqual(session.calls, [])

    def test_login_rejects_response_without_lecture_redirect(self) -> None:
        session = _FakeSession([
            _FakeResponse(url="https://ppi.example/login.php", text=LOGIN_HTML),
            _FakeResponse(url="https://ppi.example/login.php", text=LOGIN_HTML),
        ])

        with self.assertRaises(PpiAuthenticationError):
            PpiClient(base_url="https://ppi.example", session=session).login("zxabc12", "wrong")

    def test_catalog_merges_borrowed_lecture_ids_from_download_page(self) -> None:
        session = _authenticated_session([
            _FakeResponse(url="https://ppi.example/lectures.php", text=LECTURES_HTML),
            _FakeResponse(url="https://ppi.example/download.php", text=BORROWED_HTML),
        ])
        client = PpiClient(base_url="https://ppi.example", session=session)
        client.login("zxabc12", "ppi-password")

        catalog = client.fetch_lecture_catalog()

        self.assertEqual(catalog.lectures[0].id, 17)
        self.assertTrue(catalog.lectures[0].borrowed)

    def test_borrow_verifies_the_server_returned_an_entitlement(self) -> None:
        session = _authenticated_session([
            _FakeResponse(url="https://ppi.example/lectures.php", text=LECTURES_HTML),
            _FakeResponse(url="https://ppi.example/download.php", text=BORROWED_HTML),
            _FakeResponse(url="https://ppi.example/lectures.php?borrow=42", text=BORROWED_AFTER_HTML),
        ])
        client = PpiClient(base_url="https://ppi.example", session=session)
        client.login("zxabc12", "ppi-password")

        lecture = client.borrow_lecture(42)

        self.assertEqual(lecture.id, 42)
        self.assertTrue(lecture.borrowed)
        self.assertEqual(session.calls[-1].kwargs["params"], {"borrow": 42})

    def test_download_returns_zip_contract(self) -> None:
        session = _authenticated_session([
            _FakeResponse(
                url="https://ppi.example/download.php?lecture=17",
                headers={
                    "Content-Type": "application/zip",
                    "Content-Disposition": 'attachment; filename="Natural_Language_Processing.zip"',
                },
                content=b"PK\x03\x04archive",
            ),
        ])
        client = PpiClient(base_url="https://ppi.example", session=session)
        client.login("zxabc12", "ppi-password")

        download = client.download_lecture(17)

        self.assertEqual(download.filename, "Natural_Language_Processing.zip")
        self.assertEqual(download.content_type, "application/zip")
        self.assertEqual(download.data, b"PK\x03\x04archive")

    def test_download_rejects_html_without_entitlement(self) -> None:
        session = _authenticated_session([
            _FakeResponse(url="https://ppi.example/download.php?lecture=99", text=BORROWED_HTML),
        ])
        client = PpiClient(base_url="https://ppi.example", session=session)
        client.login("zxabc12", "ppi-password")

        with self.assertRaises(PpiAccessError):
            client.download_lecture(99)

    def test_token_request_requires_server_success_page(self) -> None:
        session = _authenticated_session([
            _FakeResponse(url="https://ppi.example/asktokens.php", text=TOKEN_SUCCESS_HTML),
        ])
        client = PpiClient(base_url="https://ppi.example", session=session)
        client.login("zxabc12", "ppi-password")

        result = client.request_tokens("I contributed a protocol that is still under review.")

        self.assertTrue(result.submitted)
        self.assertEqual(session.calls[-1].kwargs["data"]["message"], "I contributed a protocol that is still under review.")


def _authenticated_session(extra: list["_FakeResponse"]) -> "_FakeSession":
    return _FakeSession([
        _FakeResponse(url="https://ppi.example/login.php", text=LOGIN_HTML),
        _FakeResponse(status_code=302, url="https://ppi.example/login.php", headers={"Location": "lectures.php"}),
        *extra,
    ])


@dataclass
class _Call:
    method: str
    url: str
    kwargs: dict[str, object]


@dataclass
class _FakeResponse:
    status_code: int = 200
    url: str = "https://ppi.example/"
    text: str = ""
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "text/html; charset=UTF-8"})
    content: bytes = b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.responses = list(responses)
        self.headers: dict[str, str] = {}
        self.calls: list[_Call] = []
        self.closed = False

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        return self._request("GET", url, kwargs)

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        return self._request("POST", url, kwargs)

    def close(self) -> None:
        self.closed = True

    def _request(self, method: str, url: str, kwargs: dict[str, object]) -> _FakeResponse:
        self.calls.append(_Call(method, url, kwargs))
        if not self.responses:
            raise AssertionError(f"Unexpected {method} {url}")
        return self.responses.pop(0)


if __name__ == "__main__":
    unittest.main()

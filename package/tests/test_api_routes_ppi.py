from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper import api_routes_ppi, api_server
from tue_api_wrapper.ppi_auth import PpiConfigurationError, build_ppi_client
from tue_api_wrapper.ppi_client import PpiAccessError, PpiAuthenticationError, PpiValidationError
from tue_api_wrapper.ppi_models import (
    PpiBorrowedLecturesPage,
    PpiDownload,
    PpiLecture,
    PpiLectureCatalog,
    PpiSignupResult,
    PpiTokenRequestResult,
)


class PpiRouteTests(unittest.TestCase):
    def test_signup_request_redacts_password_in_representations(self) -> None:
        request = api_routes_ppi.PpiSignupRequest(username="zxabc12", password="ppi-password")

        self.assertNotIn("ppi-password", repr(request))

    def test_ppi_routes_are_registered(self) -> None:
        paths = {route.path for route in api_server.app.routes}

        self.assertTrue(
            {
                "/api/ppi/signup",
                "/api/ppi/lectures",
                "/api/ppi/borrowed",
                "/api/ppi/lectures/{lecture_id}/borrow",
                "/api/ppi/lectures/{lecture_id}/download",
                "/api/ppi/token-requests",
            }.issubset(paths)
        )

    def test_signup_returns_activation_contract_and_closes_client(self) -> None:
        client = _FakePpiClient()
        client.signup_result = PpiSignupResult(
            username="zxabc12",
            activation_email="zxabc12@student.uni-tuebingen.de",
        )

        with patch.object(api_routes_ppi, "_public_client", return_value=client):
            result = api_routes_ppi.ppi_signup(
                api_routes_ppi.PpiSignupRequest(username="zxabc12", password="ppi-password")
            )

        self.assertEqual(result["activation_email"], "zxabc12@student.uni-tuebingen.de")
        self.assertTrue(result["activation_required"])
        self.assertTrue(client.closed)

    def test_lecture_route_serializes_authenticated_catalog(self) -> None:
        client = _FakePpiClient()
        client.catalog = PpiLectureCatalog(
            tokens=2,
            source_url="https://ppi.example/lectures.php",
            lectures=[PpiLecture(id=42, title="Machine Learning", protocol_count=4, borrowed=False, can_borrow=True)],
        )

        with patch.object(api_routes_ppi, "_authenticated_client", return_value=client):
            result = api_routes_ppi.ppi_lectures()

        self.assertEqual(result["tokens"], 2)
        self.assertEqual(result["lectures"][0]["id"], 42)
        self.assertTrue(client.closed)

    def test_download_route_returns_attachment(self) -> None:
        client = _FakePpiClient()
        client.download = PpiDownload(
            lecture_id=42,
            filename="Machine_Learning.zip",
            content_type="application/zip",
            data=b"PK\x03\x04",
        )

        with patch.object(api_routes_ppi, "_authenticated_client", return_value=client):
            response = api_routes_ppi.ppi_download(42)

        self.assertEqual(response.body, b"PK\x03\x04")
        self.assertEqual(response.media_type, "application/zip")
        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="Machine_Learning.zip"')
        self.assertTrue(client.closed)

    def test_access_error_translates_to_forbidden(self) -> None:
        client = _FakePpiClient()
        client.borrow_error = PpiAccessError("No PPI tokens are available.")

        with patch.object(api_routes_ppi, "_authenticated_client", return_value=client):
            with self.assertRaises(HTTPException) as context:
                api_routes_ppi.ppi_borrow(42)

        self.assertEqual(context.exception.status_code, 403)
        self.assertTrue(client.closed)

    def test_missing_ppi_credentials_are_service_unavailable(self) -> None:
        with patch.dict(
            "os.environ",
            {"UNI_USERNAME": "zxabc12", "UNI_PASSWORD": "university-password"},
            clear=True,
        ):
            with self.assertRaises(PpiConfigurationError):
                build_ppi_client()

    def test_builder_uses_only_dedicated_ppi_credentials(self) -> None:
        client = _FakePpiClient()
        with patch.dict(
            "os.environ",
            {"PPI_USERNAME": "zxabc12", "PPI_PASSWORD": "ppi-password"},
            clear=True,
        ), patch("tue_api_wrapper.ppi_auth.PpiClient", return_value=client):
            result = build_ppi_client()

        self.assertIs(result, client)
        self.assertEqual(client.login_args, ("zxabc12", "ppi-password"))


class _FakePpiClient:
    def __init__(self) -> None:
        self.signup_result: PpiSignupResult | None = None
        self.catalog = PpiLectureCatalog(tokens=0, source_url="", lectures=[])
        self.borrowed = PpiBorrowedLecturesPage(tokens=0, source_url="", lectures=[])
        self.download: PpiDownload | None = None
        self.borrow_error: Exception | None = None
        self.closed = False
        self.login_args: tuple[str, str] | None = None

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def signup(self, username: str, password: str) -> PpiSignupResult:
        assert self.signup_result is not None
        return self.signup_result

    def fetch_lecture_catalog(self) -> PpiLectureCatalog:
        return self.catalog

    def fetch_borrowed_lectures(self) -> PpiBorrowedLecturesPage:
        return self.borrowed

    def borrow_lecture(self, lecture_id: int) -> PpiLecture:
        if self.borrow_error:
            raise self.borrow_error
        return PpiLecture(id=lecture_id, title="Machine Learning", protocol_count=4, borrowed=True, can_borrow=False)

    def download_lecture(self, lecture_id: int) -> PpiDownload:
        assert self.download is not None
        return self.download

    def request_tokens(self, message: str) -> PpiTokenRequestResult:
        return PpiTokenRequestResult(submitted=True)

    def close(self) -> None:
        self.closed = True


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from email.message import Message
from pathlib import PurePath
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests

from .config import DEFAULT_TIMEOUT_SECONDS
from .ppi_html import parse_borrowed_lectures, parse_lecture_catalog
from .ppi_models import (
    PpiBorrowedLecturesPage,
    PpiDownload,
    PpiLecture,
    PpiLectureCatalog,
    PpiSignupResult,
    PpiTokenRequestResult,
)

PPI_BASE_URL = "https://ppi.fsi.uni-tuebingen.de"
PPI_STUDENT_EMAIL_DOMAIN = "student.uni-tuebingen.de"
PPI_USERNAME_RE = re.compile(r"zx[a-z]{3}\d{2}", re.IGNORECASE)


class PpiError(Exception):
    pass


class PpiValidationError(PpiError, ValueError):
    pass


class PpiAuthenticationError(PpiError):
    pass


class PpiAccessError(PpiError):
    pass


class PpiClient:
    """Client for PPI's independent account and exam-protocol service."""

    def __init__(
        self,
        *,
        base_url: str = PPI_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            "tue-api-wrapper/0.4 (+https://ppi.fsi.uni-tuebingen.de/)",
        )
        self._authenticated = False

    def signup(self, username: str, password: str) -> PpiSignupResult:
        username = self._username(username)
        if not password:
            raise PpiValidationError("A non-empty, PPI-specific password is required.")

        response = self.session.get(self._url("create.php"), timeout=self.timeout)
        response.raise_for_status()
        response = self.session.post(
            self._url("create.php"),
            data={
                "username": username,
                "password": password,
                "password_repeated": password,
            },
            timeout=self.timeout,
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code not in {301, 302, 303} or self._redirect_path(response) != "/activate.php":
            message = self._page_message(response.text)
            raise PpiValidationError(f"PPI account creation failed: {message}")
        return PpiSignupResult(
            username=username,
            activation_email=f"{username}@{PPI_STUDENT_EMAIL_DOMAIN}",
        )

    def login(self, username: str, password: str) -> None:
        username = self._username(username)
        if not password:
            raise PpiAuthenticationError("A PPI password is required.")
        response = self.session.get(self._url("login.php"), timeout=self.timeout)
        response.raise_for_status()
        response = self.session.post(
            self._url("login.php"),
            data={"username": username, "password": password},
            timeout=self.timeout,
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code not in {301, 302, 303} or self._redirect_path(response) != "/lectures.php":
            raise PpiAuthenticationError("PPI rejected the username or PPI-specific password.")
        self._authenticated = True

    def restore_authenticated_session(self) -> None:
        """Mark a client with restored cookies ready for server-validated requests."""
        self._authenticated = True

    def fetch_lecture_catalog(self) -> PpiLectureCatalog:
        self._require_authenticated()
        catalog_response = self._authenticated_get("lectures.php")
        borrowed_response = self._authenticated_get("download.php")
        catalog = parse_lecture_catalog(catalog_response.text, catalog_response.url)
        borrowed = parse_borrowed_lectures(borrowed_response.text, borrowed_response.url)
        borrowed_ids = {lecture.title: lecture.id for lecture in borrowed.lectures if lecture.id is not None}
        for lecture in catalog.lectures:
            if lecture.borrowed and lecture.id is None:
                lecture.id = borrowed_ids.get(lecture.title)
        return catalog

    def fetch_borrowed_lectures(self) -> PpiBorrowedLecturesPage:
        self._require_authenticated()
        response = self._authenticated_get("download.php")
        return parse_borrowed_lectures(response.text, response.url)

    def borrow_lecture(self, lecture_id: int) -> PpiLecture:
        lecture_id = self._lecture_id(lecture_id)
        catalog = self.fetch_lecture_catalog()
        lecture = next((item for item in catalog.lectures if item.id == lecture_id), None)
        if lecture is None:
            raise PpiValidationError(f"PPI lecture {lecture_id} was not found.")
        if lecture.borrowed:
            return lecture
        if not lecture.can_borrow:
            message = "No PPI tokens are available." if catalog.tokens <= 0 else "The lecture cannot be borrowed."
            raise PpiAccessError(message)

        response = self._authenticated_get("lectures.php", params={"borrow": lecture_id})
        updated = parse_lecture_catalog(response.text, response.url)
        confirmed = next((item for item in updated.lectures if item.title == lecture.title and item.borrowed), None)
        if confirmed is None:
            raise PpiAccessError("PPI did not grant the requested lecture entitlement.")
        confirmed.id = lecture_id
        return confirmed

    def download_lecture(self, lecture_id: int) -> PpiDownload:
        self._require_authenticated()
        lecture_id = self._lecture_id(lecture_id)
        response = self._authenticated_get("download.php", params={"lecture": lecture_id})
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/zip":
            raise PpiAccessError("PPI did not return a ZIP; the lecture may not have an active entitlement.")
        return PpiDownload(
            lecture_id=lecture_id,
            filename=self._download_filename(response, lecture_id),
            content_type=content_type,
            data=response.content,
        )

    def request_tokens(self, message: str) -> PpiTokenRequestResult:
        self._require_authenticated()
        message = message.strip()
        if not message:
            raise PpiValidationError("A reason for the PPI token request is required.")
        response = self.session.post(
            self._url("asktokens.php"),
            data={"message": message},
            timeout=self.timeout,
            allow_redirects=False,
        )
        response.raise_for_status()
        self._raise_if_logged_out(response)
        text = " ".join(BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True).split()).casefold()
        if "überprüfen deinen antrag" not in text and "review your application" not in text:
            raise PpiError("PPI did not confirm the token request.")
        return PpiTokenRequestResult(submitted=True)

    def close(self) -> None:
        self.session.close()
        self._authenticated = False

    def _authenticated_get(self, path: str, **kwargs: object):
        response = self.session.get(
            self._url(path),
            timeout=self.timeout,
            allow_redirects=False,
            **kwargs,
        )
        response.raise_for_status()
        self._raise_if_logged_out(response)
        return response

    def _raise_if_logged_out(self, response) -> None:
        if response.status_code in {301, 302, 303} and self._redirect_path(response) == "/login.php":
            self._authenticated = False
            raise PpiAuthenticationError("The PPI session is not authenticated.")

    def _require_authenticated(self) -> None:
        if not self._authenticated:
            raise PpiAuthenticationError("Call login() before using authenticated PPI services.")

    def _url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path)

    @staticmethod
    def _username(username: str) -> str:
        username = username.strip().lower()
        if PPI_USERNAME_RE.fullmatch(username) is None:
            raise PpiValidationError("PPI requires a seven-character ZDV username such as zxabc12.")
        return username

    @staticmethod
    def _lecture_id(value: int) -> int:
        if value <= 0:
            raise PpiValidationError("PPI lecture IDs must be positive integers.")
        return value

    @staticmethod
    def _redirect_path(response) -> str:
        return urlparse(urljoin(response.url, response.headers.get("Location", ""))).path

    @staticmethod
    def _page_message(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one("#infoText")
        return " ".join((node or soup).get_text(" ", strip=True).split()) or "the server rejected the request"

    @staticmethod
    def _download_filename(response, lecture_id: int) -> str:
        message = Message()
        message["Content-Disposition"] = response.headers.get("Content-Disposition", "")
        filename = message.get_filename() or f"ppi-lecture-{lecture_id}.zip"
        return PurePath(filename).name

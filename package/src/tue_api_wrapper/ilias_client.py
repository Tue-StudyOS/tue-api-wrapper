from __future__ import annotations

from urllib.parse import urljoin, urlparse

import requests

from .config import AlmaLoginError, AlmaParseError, DEFAULT_TIMEOUT_SECONDS
from .ilias_html import (
    extract_hidden_form,
    extract_idp_error,
    extract_idp_login_form,
    extract_shib_login_url,
    is_authenticated_ilias_page,
    parse_ilias_content_page,
    parse_ilias_root_page,
)
from .ilias_course_client import fetch_assignment_deadlines, fetch_course_assignments
from .ilias_course_models import IliasAssignmentDeadline, IliasCourseAssignmentsPage
from .ilias_learning_html import (
    parse_exercise_assignments,
    parse_forum_topics,
    parse_membership_overview,
    parse_task_overview,
)
from .models import (
    IliasContentPage,
    IliasExerciseAssignment,
    IliasForumTopic,
    IliasMembershipItem,
    IliasRootPage,
    IliasTaskItem,
)

ILIAS_BASE_URL = "https://ovidius.uni-tuebingen.de/"
ILIAS_LOGIN_URL = ILIAS_BASE_URL + "login.php?cmd=force_login"
ILIAS_ROOT_URL = ILIAS_BASE_URL + "goto.php/root/1"
ILIAS_MEMBERSHIP_URL = ILIAS_BASE_URL + "ilias.php?baseClass=ilmembershipoverviewgui"
ILIAS_TASK_URL = ILIAS_BASE_URL + "ilias.php?baseClass=ilderivedtasksgui"
SAML_RESPONSE_FIELD = "SAML" + "Response"
RELAY_STATE_FIELD = "RelayState"


class IliasClient:
    def __init__(
        self,
        *,
        login_url: str = ILIAS_LOGIN_URL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.login_url = login_url
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            "tue-api-wrapper/0.1 (+https://ovidius.uni-tuebingen.de/)",
        )

    def login(self, username: str, password: str) -> IliasRootPage:
        response = self.session.get(self.login_url, timeout=self.timeout_seconds)
        response.raise_for_status()

        shib_login_url = extract_shib_login_url(response.text, response.url)
        response = self.session.get(shib_login_url, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()

        idp_form = extract_idp_login_form(response.text, response.url)
        payload = dict(idp_form.payload)
        payload["j_username"] = username
        payload["j_password"] = password
        payload["_eventId_proceed"] = payload.get("_eventId_proceed", "")

        response = self.session.post(
            idp_form.action_url,
            data=payload,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()

        error = extract_idp_error(response.text)
        if error:
            raise AlmaLoginError(error)

        response = self._complete_saml_handoff(response)
        return parse_ilias_root_page(response.text, response.url)

    def fetch_root_page(self) -> IliasRootPage:
        response = self.session.get(
            ILIAS_ROOT_URL,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_ilias_root_page(response.text, response.url)

    def fetch_content_page(self, target: str) -> IliasContentPage:
        response = self.session.get(
            self._normalize_target_url(target),
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_ilias_content_page(response.text, response.url)

    def fetch_forum_topics(self, target: str) -> tuple[IliasForumTopic, ...]:
        response = self.session.get(
            self._normalize_target_url(target),
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_forum_topics(response.text, response.url)

    def fetch_exercise_assignments(self, target: str) -> tuple[IliasExerciseAssignment, ...]:
        response = self.session.get(
            self._normalize_target_url(target),
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_exercise_assignments(response.text, response.url)

    def fetch_course_assignments(self, target: str) -> IliasCourseAssignmentsPage:
        return fetch_course_assignments(self, target)

    def fetch_assignment_deadlines(
        self,
        *,
        course_limit: int = 20,
        assignment_limit: int = 50,
    ) -> tuple[IliasAssignmentDeadline, ...]:
        return fetch_assignment_deadlines(self, course_limit=course_limit, assignment_limit=assignment_limit)

    def fetch_membership_overview(self) -> tuple[IliasMembershipItem, ...]:
        response = self.session.get(
            ILIAS_MEMBERSHIP_URL,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_membership_overview(response.text, response.url)

    def fetch_task_overview(self) -> tuple[IliasTaskItem, ...]:
        response = self.session.get(
            ILIAS_TASK_URL,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        return parse_task_overview(response.text, response.url)

    def _complete_saml_handoff(self, response: requests.Response) -> requests.Response:
        for _ in range(6):
            if is_authenticated_ilias_page(response.text, response.url):
                return response

            parsed = urlparse(response.url)
            if SAML_RESPONSE_FIELD in response.text and RELAY_STATE_FIELD in response.text:
                form = extract_hidden_form(response.text, response.url, {SAML_RESPONSE_FIELD, RELAY_STATE_FIELD})
                response = self.session.post(
                    form.action_url,
                    data=form.payload,
                    timeout=self.timeout_seconds,
                    allow_redirects=True,
                )
                response.raise_for_status()
                continue

            if parsed.netloc == "idp.uni-tuebingen.de" and "_eventId_proceed" in response.text:
                form = extract_hidden_form(response.text, response.url, {"_eventId_proceed"})
                response = self.session.post(
                    form.action_url,
                    data=form.payload,
                    timeout=self.timeout_seconds,
                    allow_redirects=True,
                )
                response.raise_for_status()
                continue

            break

        raise AlmaParseError("Could not complete the ILIAS SAML handoff into an authenticated page.")

    @staticmethod
    def _normalize_target_url(target: str) -> str:
        target = target.strip()
        if not target:
            raise AlmaParseError("A non-empty ILIAS target is required.")
        if target.startswith(("http://", "https://")):
            return target
        if target.startswith("goto.php/"):
            return urljoin(ILIAS_BASE_URL, target)
        return urljoin(ILIAS_BASE_URL + "goto.php/", target.lstrip("/"))

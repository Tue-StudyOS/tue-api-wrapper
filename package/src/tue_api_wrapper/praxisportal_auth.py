from __future__ import annotations

from urllib.parse import urlparse

import requests

from .config import AlmaLoginError, AlmaParseError
from .ilias_html import extract_hidden_form, extract_idp_error, extract_idp_login_form
from .praxisportal_models import CareerSubscription, CareerUser

PRAXISPORTAL_BASE_URL = "https://www.praxisportal.uni-tuebingen.de"
SAML_RESPONSE_FIELD = "SAML" + "Response"
RELAY_STATE_FIELD = "RelayState"


class PraxisportalAuthMixin:
    timeout: int
    session: requests.Session

    def login(self, username: str, password: str) -> CareerUser:
        response = self.session.get(
            f"{PRAXISPORTAL_BASE_URL}/shibboleth",
            params={"lang": "de"},
            timeout=self.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        form = extract_idp_login_form(response.text, response.url)
        payload = dict(form.payload)
        payload["j_username"] = username
        payload["j_password"] = password
        payload["_eventId_proceed"] = payload.get("_eventId_proceed", "")
        response = self.session.post(form.action_url, data=payload, timeout=self.timeout, allow_redirects=True)
        response.raise_for_status()
        error = extract_idp_error(response.text)
        if error:
            raise AlmaLoginError(error)
        self._complete_saml_handoff(response)
        return self.fetch_current_user()

    def fetch_current_user(self) -> CareerUser:
        response = self.session.get(
            f"{PRAXISPORTAL_BASE_URL}/1/user",
            headers={"Accept": "application/json, text/plain, */*"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json().get("user", {})
        return CareerUser(
            id=int(payload["id"]),
            username=str(payload.get("username", "")).strip(),
            fullname=str(payload.get("fullname", "")).strip(),
            institute_id=int(payload["institute_id"]) if payload.get("institute_id") is not None else None,
        )

    def fetch_my_subscriptions(self) -> list[CareerSubscription]:
        user = self.fetch_current_user()
        response = self.session.get(
            f"{PRAXISPORTAL_BASE_URL}/1/subscription/user/{user.id}",
            headers={"Accept": "application/json, text/plain, */*"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        from .praxisportal_subscriptions import map_praxisportal_subscription

        return [map_praxisportal_subscription(item) for item in response.json().get("subscriptions", [])]

    def _complete_saml_handoff(self, response: requests.Response) -> None:
        for _ in range(6):
            if self._is_authenticated_page(response):
                return
            parsed = urlparse(response.url)
            if SAML_RESPONSE_FIELD in response.text and RELAY_STATE_FIELD in response.text:
                form = extract_hidden_form(response.text, response.url, {SAML_RESPONSE_FIELD, RELAY_STATE_FIELD})
                response = self.session.post(form.action_url, data=form.payload, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                continue
            if parsed.netloc == "idp.uni-tuebingen.de" and "_eventId_proceed" in response.text:
                form = extract_hidden_form(response.text, response.url, {"_eventId_proceed"})
                response = self.session.post(form.action_url, data=form.payload, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                continue
            break
        raise AlmaParseError("Could not complete the Praxisportal SAML handoff into an authenticated page.")

    @staticmethod
    def _is_authenticated_page(response: requests.Response) -> bool:
        parsed = urlparse(response.url)
        if parsed.netloc != "www.praxisportal.uni-tuebingen.de":
            return False
        return "j_username" not in response.text and SAML_RESPONSE_FIELD not in response.text

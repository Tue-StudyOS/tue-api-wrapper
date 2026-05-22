from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_documents_html import extract_studyservice_page
from tue_api_wrapper.alma_profile_client import fetch_student_profile


class _FakeResponse:
    url = "https://alma.example/alma/pages/cm/stu/studyService/start.xhtml"

    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, pages: tuple[str, ...]) -> None:
        self._pages = list(pages)
        self.posts: list[dict[str, str]] = []

    def get(self, _url: str, timeout: int):
        return _FakeResponse(self._pages.pop(0))

    def post(self, _url: str, data: dict[str, str], timeout: int, allow_redirects: bool):
        self.posts.append(data)
        return _FakeResponse(self._pages.pop(0))


class _FakeClient:
    studyservice_url = "https://alma.example/studyservice"
    timeout_seconds = 10

    def __init__(self, pages: tuple[str, ...]) -> None:
        self.session = _FakeSession(pages)

    @staticmethod
    def _looks_logged_out(_html: str) -> bool:
        return False


class AlmaProfileTests(unittest.TestCase):
    def test_extracts_contact_sections_email_and_address_without_guessing(self) -> None:
        html = """
        <form id="studyserviceForm" action="/alma/studyservice">
          <input type="hidden" name="javax.faces.ViewState" value="e2s4" />
          <h2>Personendaten: Sebastian Böhler</h2>
          <button type="submit" name="studyserviceForm:content.5" class="tabButton active">Kontaktdaten</button>
          <fieldset>
            <legend>Kontakt</legend>
            <table>
              <tr><td>E-Mail</td><td>s.boehler<img alt="At" />student.uni-tuebingen.de</td></tr>
              <tr><td>Semesteranschrift</td><td>Wilhelmstr. 1<br />72074 Tübingen</td></tr>
            </table>
          </fieldset>
        </form>
        """

        page = extract_studyservice_page(html, "https://alma.example/studyservice")

        self.assertEqual(page.person_name, "Sebastian Böhler")
        self.assertEqual(page.contact_sections[0].title, "Kontakt")
        self.assertEqual(page.contact_sections[0].fields[0].value, "s.boehler@student.uni-tuebingen.de")
        self.assertEqual(page.contact_sections[0].fields[1].value, "Wilhelmstr. 1\n72074 Tübingen")

    def test_fetch_student_profile_switches_to_contact_tab_and_returns_visible_values(self) -> None:
        start_html = """
        <form id="studyserviceForm" action="/alma/studyservice">
          <input type="hidden" name="javax.faces.ViewState" value="start" />
          <h2>Personendaten: Sebastian Böhler</h2>
          <button type="submit" name="studyserviceForm:content.5" class="tabButton">Kontaktdaten</button>
          <button type="submit" name="studyserviceForm:content.10" class="tabButton active">Bescheide</button>
          <button name="studyserviceForm:report:reports:0:job2" type="submit">
            <span class="jobname">Immatrikulationsbescheinigung [PDF]</span>
          </button>
        </form>
        """
        contact_html = """
        <form id="studyserviceForm" action="/alma/studyservice">
          <input type="hidden" name="javax.faces.ViewState" value="contact" />
          <h2>Personendaten: Sebastian Böhler</h2>
          <button type="submit" name="studyserviceForm:content.5" class="tabButton active">Kontaktdaten</button>
          <fieldset>
            <legend>Kontakt</legend>
            <table>
              <tr><td>E-Mail</td><td>s.boehler@student.uni-tuebingen.de</td></tr>
              <tr><td>Heimatanschrift</td><td>Main Street 8<br />72076 Tübingen</td></tr>
            </table>
          </fieldset>
        </form>
        """

        client = _FakeClient((start_html, contact_html))
        profile = fetch_student_profile(client)

        self.assertEqual(client.session.posts[0]["activePageElementId"], "studyserviceForm:content.5")
        self.assertEqual(profile.person_name, "Sebastian Böhler")
        self.assertEqual(profile.email_addresses, ("s.boehler@student.uni-tuebingen.de",))
        self.assertEqual(profile.postal_addresses, ("Main Street 8\n72076 Tübingen",))


if __name__ == "__main__":
    unittest.main()

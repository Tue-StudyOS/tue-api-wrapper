from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.ilias_html import extract_hidden_form, is_authenticated_ilias_page


class IliasAuthTests(unittest.TestCase):
    def test_hidden_form_can_use_submit_button_as_required_field(self) -> None:
        html = """
        <form action="/idp/profile/SAML2/Redirect/SSO?execution=e1s2" method="post">
          <input type="hidden" name="csrf_token" value="abc" />
          <button name="_eventId_proceed" type="submit">Continue</button>
        </form>
        """
        form = extract_hidden_form(
            html,
            "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s2",
            {"_eventId_proceed"},
        )

        self.assertEqual(form.payload["_eventId_proceed"], "")
        self.assertEqual(form.payload["csrf_token"], "abc")

    def test_authenticated_detector_accepts_navigation_markers(self) -> None:
        html = """
        <html>
          <head><title>Dashboard</title></head>
          <body>
            <ul class="il-mainbar-entries"></ul>
            <a href="logout.php?baseClass=ilstartupgui">Abmelden</a>
          </body>
        </html>
        """

        self.assertTrue(
            is_authenticated_ilias_page(html, "https://ovidius.uni-tuebingen.de/goto.php/root/1")
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper import api_routes_edit_actions, api_server
from tue_api_wrapper.portal_cache import CacheConfig, PortalCache
from tue_api_wrapper.portal_service import PortalService, clear_portal_cache, configure_portal_cache


class PortalCacheTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_portal_cache()
        configure_portal_cache(enabled=False, ttl_seconds=60.0)

    def test_disabled_cache_keeps_loading(self) -> None:
        service = PortalService(cache=PortalCache(CacheConfig(enabled=False, ttl_seconds=30.0)))
        calls = {"count": 0}

        with patch("tue_api_wrapper.portal_service.read_uni_credentials", return_value=("student", "secret")), patch(
            "tue_api_wrapper.portal_service.read_mail_credentials",
            return_value=("student", "secret"),
        ), patch(
            "tue_api_wrapper.portal_service.build_dashboard_payload",
            side_effect=lambda **_: self._dashboard(calls),
        ):
            first = service.build_dashboard(term_label="Sommer 2026")
            second = service.build_dashboard(term_label="Sommer 2026")

        self.assertEqual(first["call"], 1)
        self.assertEqual(second["call"], 2)
        self.assertEqual(calls["count"], 2)

    def test_enabled_cache_reuses_dashboard_until_ttl_expires(self) -> None:
        now = {"value": 100.0}
        cache = PortalCache(CacheConfig(enabled=True, ttl_seconds=10.0), clock=lambda: now["value"])
        service = PortalService(cache=cache)
        calls = {"count": 0}

        with patch("tue_api_wrapper.portal_service.read_uni_credentials", return_value=("student", "secret")), patch(
            "tue_api_wrapper.portal_service.read_mail_credentials",
            return_value=("student", "secret"),
        ), patch(
            "tue_api_wrapper.portal_service.build_dashboard_payload",
            side_effect=lambda **_: self._dashboard(calls),
        ):
            first = service.build_dashboard(term_label="Sommer 2026")
            second = service.build_dashboard(term_label="Sommer 2026")
            now["value"] = 111.0
            third = service.build_dashboard(term_label="Sommer 2026")

        self.assertEqual(first["call"], 1)
        self.assertEqual(second["call"], 1)
        self.assertEqual(third["call"], 2)
        self.assertEqual(calls["count"], 2)

    def test_cache_isolated_by_parameters_and_credentials(self) -> None:
        service = PortalService(cache=PortalCache(CacheConfig(enabled=True, ttl_seconds=30.0)))
        calls = {"count": 0}
        credentials = {"uni": ("student-a", "secret-a"), "mail": ("student-a", "secret-a")}

        def fake_uni_credentials():
            return credentials["uni"]

        def fake_mail_credentials():
            return credentials["mail"]

        with patch("tue_api_wrapper.portal_service.read_uni_credentials", side_effect=fake_uni_credentials), patch(
            "tue_api_wrapper.portal_service.read_mail_credentials",
            side_effect=fake_mail_credentials,
        ), patch(
            "tue_api_wrapper.portal_service.build_dashboard_payload",
            side_effect=lambda **_: self._dashboard(calls),
        ):
            service.build_dashboard(term_label="Sommer 2026")
            service.build_dashboard(term_label="Winter 2025/26")
            credentials["uni"] = ("student-b", "secret-b")
            credentials["mail"] = ("student-b", "secret-b")
            service.build_dashboard(term_label="Sommer 2026")

        self.assertEqual(calls["count"], 3)

    def test_mutation_route_invalidates_cached_dashboard(self) -> None:
        calls = {"count": 0}
        configure_portal_cache(enabled=True, ttl_seconds=60.0)

        with patch("tue_api_wrapper.portal_service.read_uni_credentials", return_value=("student", "secret")), patch(
            "tue_api_wrapper.portal_service.read_mail_credentials",
            return_value=("student", "secret"),
        ), patch(
            "tue_api_wrapper.portal_service.build_dashboard_payload",
            side_effect=lambda **_: self._dashboard(calls),
        ), patch.object(
            api_routes_edit_actions.portal_service,
            "_ilias_client",
            return_value=object(),
        ), patch(
            "tue_api_wrapper.api_routes_edit_actions.add_to_favorites",
            return_value={"status": "submitted"},
        ):
            first = api_server.portal_service.build_dashboard(term_label="Sommer 2026")
            second = api_server.portal_service.build_dashboard(term_label="Sommer 2026")
            mutation = api_routes_edit_actions.ilias_add_favorite(
                url="https://ovidius.uni-tuebingen.de/ilias.php?cmd=addToDesk",
            )
            third = api_server.portal_service.build_dashboard(term_label="Sommer 2026")

        self.assertEqual(first["call"], 1)
        self.assertEqual(second["call"], 1)
        self.assertEqual(mutation["status"], "submitted")
        self.assertEqual(third["call"], 2)
        self.assertEqual(calls["count"], 2)

    @staticmethod
    def _dashboard(calls: dict[str, int]) -> dict[str, object]:
        calls["count"] += 1
        return {"call": calls["count"], "items": []}


if __name__ == "__main__":
    unittest.main()

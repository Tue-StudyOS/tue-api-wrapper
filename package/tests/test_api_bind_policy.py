from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper import api_server


class ApiBindPolicyTests(unittest.TestCase):
    def test_credentials_prevent_network_bind_before_server_starts(self) -> None:
        for host in ("0.0.0.0", "::", "192.168.1.2", "api.example.org", ""):
            for name in ("UNI_USERNAME", "UNI_PASSWORD", "ALMA_PASSWORD", "ILIAS_PASSWORD"):
                with self.subTest(host=host, credential=name):
                    with patch.dict(os.environ, {"HOST": host, name: "test-value"}, clear=True):
                        with patch.object(api_server.uvicorn, "run") as run:
                            with self.assertRaisesRegex(ValueError, "non-loopback"):
                                api_server.main()
                            run.assert_not_called()

    def test_local_authenticated_server_remains_available(self) -> None:
        for host in ("127.0.0.1", "127.0.0.2", "::1", "localhost"):
            with self.subTest(host=host):
                env = {"HOST": host, "UNI_USERNAME": "student", "UNI_PASSWORD": "test-value"}
                with patch.dict(os.environ, env, clear=True):
                    with patch.object(api_server.uvicorn, "run") as run:
                        api_server.main()
                        self.assertEqual(run.call_args.kwargs["host"], host)

    def test_public_data_server_can_bind_without_university_credentials(self) -> None:
        with patch.dict(os.environ, {"HOST": "0.0.0.0"}, clear=True):
            with patch.object(api_server.uvicorn, "run") as run:
                api_server.main()
                self.assertEqual(run.call_args.kwargs["host"], "0.0.0.0")


if __name__ == "__main__":
    unittest.main()

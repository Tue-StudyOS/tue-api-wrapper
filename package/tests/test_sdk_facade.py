from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.sdk import TuebingenPublicClient, UniversityCredentials
from tue_api_wrapper.sdk.authenticated import AuthenticatedIliasApi
from tue_api_wrapper.sdk.public import PublicAlmaApi


class SdkFacadeTests(unittest.TestCase):
    def test_credentials_from_env_file_reads_university_login(self) -> None:
        env_file = ROOT / "tmp-test.env"
        env_file.write_text(
            "\n".join(
                [
                    'export UNI_USERNAME="student"',
                    "UNI_PASSWORD='secret'",
                ]
            ),
            encoding="utf-8",
        )
        self.addCleanup(env_file.unlink)

        credentials = UniversityCredentials.from_env(env_file)

        self.assertEqual(credentials.username, "student")
        self.assertEqual(credentials.password, "secret")

    def test_credentials_model_has_single_login_pair(self) -> None:
        credentials = UniversityCredentials("student", "secret")

        self.assertEqual(credentials.username, "student")
        self.assertEqual(credentials.password, "secret")

    def test_public_client_exposes_clear_module_search_method(self) -> None:
        fake_alma = _FakePublicAlmaClient()
        client = TuebingenPublicClient(alma=PublicAlmaApi(client=fake_alma))

        result = client.alma.search_modules("machine learning", max_results=5)

        self.assertEqual(result, {"query": "machine learning", "max_results": 5})

    def test_public_campus_exposes_gym_alias(self) -> None:
        from tue_api_wrapper.sdk.public import PublicCampusApi

        client = TuebingenPublicClient(campus=PublicCampusApi(fitness_client=_FakeFitnessClient()))

        self.assertEqual(client.campus.gym_occupancy(), {"count": 42})

    def test_authenticated_ilias_exposes_course_assignments(self) -> None:
        api = AuthenticatedIliasApi(UniversityCredentials("student", "secret"), _client=_FakeIliasClient())

        self.assertEqual(api.course_assignments("crs/5551408"), {"target": "crs/5551408"})
        self.assertEqual(
            api.assignment_deadlines(course_limit=3, assignment_limit=7),
            {"course_limit": 3, "assignment_limit": 7},
        )


class _FakePublicAlmaClient:
    def search_public_module_descriptions(self, *, query: str, max_results: int):
        return {"query": query, "max_results": max_results}


class _FakeFitnessClient:
    def fetch_kuf_training_occupancy(self):
        return {"count": 42}


class _FakeIliasClient:
    def fetch_course_assignments(self, target: str):
        return {"target": target}

    def fetch_assignment_deadlines(self, *, course_limit: int = 20, assignment_limit: int = 50):
        return {"course_limit": course_limit, "assignment_limit": assignment_limit}


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.api_routes_feedback import (  # noqa: E402
    AppFeedbackIssueRequest,
    GitHubCreatedIssue,
    GitHubFeedbackConfigurationError,
    NormalizedAppFeedbackIssue,
    create_feedback_issue,
    feedback_issue_client,
    feedback_rate_limiter,
    get_feedback_status,
)


class FeedbackAPITests(unittest.TestCase):
    def setUp(self) -> None:
        feedback_rate_limiter.reset()

    def test_creates_feedback_issue(self) -> None:
        with patch.object(
            feedback_issue_client,
            "create_issue",
            return_value=GitHubCreatedIssue(
                number=42,
                url="https://github.com/SebastianBoehler/tue-api-wrapper/issues/42",
                title="[iOS Feedback] Bug: Settings submit button is clipped",
            ),
        ) as create_issue:
            response = create_feedback_issue(
                AppFeedbackIssueRequest(**_payload(title="  Settings submit button is clipped  ")),
                _request("203.0.113.10"),
            )

        self.assertEqual(
            response.model_dump(),
            {"issueNumber": 42, "issueURL": "https://github.com/SebastianBoehler/tue-api-wrapper/issues/42", "title": "[iOS Feedback] Bug: Settings submit button is clipped"},
        )

        submitted = create_issue.call_args.args[0]
        self.assertIsInstance(submitted, NormalizedAppFeedbackIssue)
        self.assertEqual(submitted.title, "Settings submit button is clipped")
        self.assertEqual(submitted.area, "Settings")
        self.assertEqual(submitted.category_label, "Bug")
        self.assertIn("<!-- source: tue-api-ios-feedback -->", submitted.github_body())

    def test_creates_desktop_feedback_issue(self) -> None:
        with patch.object(
            feedback_issue_client,
            "create_issue",
            return_value=GitHubCreatedIssue(
                number=9,
                url="https://github.com/SebastianBoehler/tue-api-wrapper/issues/9",
                title="[Desktop Feedback] Bug: Feedback form is missing a field",
            ),
        ) as create_issue:
            response = create_feedback_issue(
                AppFeedbackIssueRequest(**_payload(platform="desktop", title="Feedback form is missing a field")),
                _request("203.0.113.15"),
            )

        self.assertEqual(
            response.model_dump(),
            {"issueNumber": 9, "issueURL": "https://github.com/SebastianBoehler/tue-api-wrapper/issues/9", "title": "[Desktop Feedback] Bug: Feedback form is missing a field"},
        )

        submitted = create_issue.call_args.args[0]
        self.assertIsInstance(submitted, NormalizedAppFeedbackIssue)
        self.assertEqual(submitted.platform, "desktop")
        self.assertTrue(submitted.github_title.startswith("[Desktop Feedback]"))
        self.assertIn("<!-- source: tue-api-desktop-feedback -->", submitted.github_body())
        self.assertIn("Submitted from the Desktop feedback form.", submitted.github_body())

    def test_rejects_blank_trimmed_title(self) -> None:
        with self.assertRaises(HTTPException) as context:
            create_feedback_issue(
                AppFeedbackIssueRequest(**_payload(title="     ")),
                _request("203.0.113.11"),
            )

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(context.exception.detail, "title must not be empty.")

    def test_maps_missing_backend_configuration_to_503(self) -> None:
        with patch.object(
            feedback_issue_client,
            "create_issue",
            side_effect=GitHubFeedbackConfigurationError("Set GITHUB_FEEDBACK_TOKEN."),
        ), self.assertRaises(HTTPException) as context:
            create_feedback_issue(
                AppFeedbackIssueRequest(**_payload()),
                _request("203.0.113.12"),
            )

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "Set GITHUB_FEEDBACK_TOKEN.")

    def test_feedback_status_is_disabled_without_token(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            response = get_feedback_status()

        self.assertEqual(
            response.model_dump(),
            {
                "enabled": False,
                "repository": "SebastianBoehler/tue-api-wrapper",
                "detail": "GitHub feedback issue creation is not enabled on this backend.",
            },
        )

    def test_feedback_status_is_enabled_with_token(self) -> None:
        with patch.dict(
            os.environ,
            {
                "GITHUB_FEEDBACK_TOKEN": "ghp_test",
                "GITHUB_FEEDBACK_REPOSITORY": "example/study-hub",
            },
            clear=True,
        ):
            response = get_feedback_status()

        self.assertEqual(
            response.model_dump(),
            {
                "enabled": True,
                "repository": "example/study-hub",
                "detail": "GitHub feedback issue creation is enabled.",
            },
        )

    def test_feedback_status_rejects_invalid_repository(self) -> None:
        with patch.dict(
            os.environ,
            {
                "GITHUB_FEEDBACK_TOKEN": "ghp_test",
                "GITHUB_FEEDBACK_REPOSITORY": "invalid",
            },
            clear=True,
        ):
            response = get_feedback_status()

        self.assertEqual(
            response.model_dump(),
            {
                "enabled": False,
                "repository": None,
                "detail": "GitHub feedback repository configuration is invalid.",
            },
        )

    def test_rate_limits_repeated_submissions_from_same_sender(self) -> None:
        with patch.object(
            feedback_issue_client,
            "create_issue",
            return_value=GitHubCreatedIssue(
                number=7,
                url="https://github.com/SebastianBoehler/tue-api-wrapper/issues/7",
                title="[iOS Feedback] Feature: Better timetable filters",
            ),
        ) as create_issue:
            for index in range(3):
                response = create_feedback_issue(
                    AppFeedbackIssueRequest(**_payload(title=f"Feedback {index + 1}")),
                    _request("203.0.113.13"),
                )
                self.assertEqual(response.issueNumber, 7)

            with self.assertRaises(HTTPException) as context:
                create_feedback_issue(
                    AppFeedbackIssueRequest(**_payload(title="Feedback 4")),
                    _request("203.0.113.13"),
                )

        self.assertEqual(create_issue.call_count, 3)
        self.assertEqual(context.exception.status_code, 429)
        self.assertEqual(context.exception.detail, "Too many feedback submissions from this sender. Try again later.")
        self.assertIn("Retry-After", context.exception.headers)


def _payload(*, platform: str = "ios", title: str = "Add a darker timetable theme") -> dict[str, str]:
    return {
        "platform": platform,
        "category": "bug",
        "title": title,
        "summary": "The action button in Settings overlaps the keyboard when VoiceOver is enabled.",
        "area": "Settings",
        "expectedBehavior": "The primary button should remain visible above the keyboard.",
        "reproductionSteps": "1. Open Settings.\n2. Enable VoiceOver.\n3. Focus the password field.",
        "appVersion": "0.1.0",
        "buildNumber": "1",
        "systemVersion": "iOS 17.5",
        "deviceModel": "iPhone",
    }


def _request(sender: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/feedback/issues",
            "headers": [(b"x-forwarded-for", sender.encode())],
            "client": (sender, 12345),
        }
    )


if __name__ == "__main__":
    unittest.main()

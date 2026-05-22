from __future__ import annotations

import os
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from typing import Literal

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()

DEFAULT_GITHUB_FEEDBACK_REPOSITORY = "SebastianBoehler/tue-api-wrapper"
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
FEEDBACK_SOURCE_MARKERS: dict[str, str] = {
    "ios": "tue-api-ios-feedback",
    "desktop": "tue-api-desktop-feedback",
    "web": "tue-api-web-feedback",
}


class AppFeedbackIssueRequest(BaseModel):
    platform: Literal["ios", "desktop", "web"] = "ios"
    category: Literal["bug", "feature", "improvement", "other"]
    title: str = Field(min_length=4, max_length=120)
    summary: str = Field(min_length=10, max_length=2000)
    area: str | None = Field(default=None, max_length=80)
    expectedBehavior: str | None = Field(default=None, max_length=1200)
    reproductionSteps: str | None = Field(default=None, max_length=2000)
    appVersion: str = Field(min_length=1, max_length=40)
    buildNumber: str = Field(min_length=1, max_length=40)
    systemVersion: str = Field(min_length=1, max_length=60)
    deviceModel: str = Field(min_length=1, max_length=60)


class AppFeedbackIssueResponse(BaseModel):
    issueNumber: int
    issueURL: str
    title: str


class GitHubFeedbackConfigurationError(RuntimeError):
    pass


class GitHubFeedbackDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubCreatedIssue:
    number: int
    url: str
    title: str


@dataclass(frozen=True)
class NormalizedAppFeedbackIssue:
    platform: str
    category: str
    title: str
    summary: str
    area: str | None
    expected_behavior: str | None
    reproduction_steps: str | None
    app_version: str
    build_number: str
    system_version: str
    device_model: str

    @classmethod
    def from_request(cls, payload: AppFeedbackIssueRequest) -> "NormalizedAppFeedbackIssue":
        title = _trimmed_required(payload.title, field_name="title")
        summary = _trimmed_required(payload.summary, field_name="summary")
        return cls(
            platform=payload.platform,
            category=payload.category,
            title=title,
            summary=summary,
            area=_trimmed_optional(payload.area),
            expected_behavior=_trimmed_optional(payload.expectedBehavior),
            reproduction_steps=_trimmed_optional(payload.reproductionSteps),
            app_version=_trimmed_required(payload.appVersion, field_name="appVersion"),
            build_number=_trimmed_required(payload.buildNumber, field_name="buildNumber"),
            system_version=_trimmed_required(payload.systemVersion, field_name="systemVersion"),
            device_model=_trimmed_required(payload.deviceModel, field_name="deviceModel"),
        )

    @property
    def platform_label(self) -> str:
        return {
            "ios": "iOS",
            "desktop": "Desktop",
            "web": "Web",
        }.get(self.platform, self.platform)

    @property
    def source_marker(self) -> str:
        return FEEDBACK_SOURCE_MARKERS.get(self.platform, FEEDBACK_SOURCE_MARKERS["ios"])

    @property
    def github_title(self) -> str:
        return f"[{self.platform_label} Feedback] {self.category_label}: {self.title}"

    @property
    def category_label(self) -> str:
        return {
            "bug": "Bug",
            "feature": "Feature",
            "improvement": "Improvement",
            "other": "Other",
        }[self.category]

    def github_body(self) -> str:
        submitted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        submitted_from = (
            "the iOS in-app feedback sheet"
            if self.platform == "ios"
            else f"the {self.platform_label} feedback form"
        )
        parts = [
            f"<!-- source: {self.source_marker} -->",
            f"<!-- platform: {self.platform} -->",
            "## Summary",
            self.summary,
            "## Context",
            f"- Category: {self.category_label}",
            f"- Area: {self.area or 'Not specified'}",
            f"- App version: {self.app_version} ({self.build_number})",
            f"- OS version: {self.system_version}",
            f"- Device: {self.device_model}",
            f"- Submitted at: {submitted_at}",
        ]

        if self.reproduction_steps:
            parts.extend(["## Reproduction Steps", self.reproduction_steps])
        if self.expected_behavior:
            parts.extend(["## Expected Behavior", self.expected_behavior])

        parts.extend(
            [
                "## Notes",
                f"- Submitted from {submitted_from}.",
                "- Avoid posting personal data, credentials, or student records in follow-up comments.",
            ]
        )
        return "\n\n".join(parts)


class GitHubFeedbackIssueClient:
    def create_issue(self, feedback: NormalizedAppFeedbackIssue) -> GitHubCreatedIssue:
        repository = os.getenv("GITHUB_FEEDBACK_REPOSITORY", DEFAULT_GITHUB_FEEDBACK_REPOSITORY).strip()
        token = os.getenv("GITHUB_FEEDBACK_TOKEN", "").strip()

        if not token:
            raise GitHubFeedbackConfigurationError(
                "GitHub feedback issue creation is not configured. Set GITHUB_FEEDBACK_TOKEN on the backend host."
            )
        if repository.count("/") != 1:
            raise GitHubFeedbackConfigurationError(
                "GITHUB_FEEDBACK_REPOSITORY must use the owner/name format."
            )

        response = requests.post(
            f"{GITHUB_API_BASE_URL}/repos/{repository}/issues",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
            },
            json={
                "title": feedback.github_title,
                "body": feedback.github_body(),
            },
            timeout=12,
        )

        if response.status_code != 201:
            raise GitHubFeedbackDeliveryError(_github_error_message(response))

        payload = response.json()
        return GitHubCreatedIssue(
            number=int(payload["number"]),
            url=str(payload["html_url"]),
            title=str(payload["title"]),
        )


class FeedbackRateLimiter:
    def __init__(self, *, max_events: int = 3, window_seconds: int = 1800) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> int | None:
        now = monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()
            if len(events) >= self.max_events:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return retry_after
            events.append(now)
        return None

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


feedback_issue_client = GitHubFeedbackIssueClient()
feedback_rate_limiter = FeedbackRateLimiter()


@router.post("/api/feedback/issues", status_code=201, response_model=AppFeedbackIssueResponse)
def create_feedback_issue(payload: AppFeedbackIssueRequest, request: Request) -> AppFeedbackIssueResponse:
    sender_key = _sender_key(request)
    retry_after = feedback_rate_limiter.check(sender_key)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many feedback submissions from this sender. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        feedback = NormalizedAppFeedbackIssue.from_request(payload)
        issue = feedback_issue_client.create_issue(feedback)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except GitHubFeedbackConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (GitHubFeedbackDeliveryError, requests.RequestException) as error:
        raise HTTPException(status_code=502, detail=f"GitHub issue creation failed: {error}") from error

    return AppFeedbackIssueResponse(
        issueNumber=issue.number,
        issueURL=issue.url,
        title=issue.title,
    )


def _sender_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_sender = forwarded_for.split(",", 1)[0].strip()
    if forwarded_sender:
        return forwarded_sender
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _trimmed_required(value: str, *, field_name: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field_name} must not be empty.")
    return trimmed


def _trimmed_optional(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _github_error_message(response: requests.Response) -> str:
    message = ""
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        raw_message = payload.get("message")
        if isinstance(raw_message, str):
            message = raw_message.strip()

    if not message:
        message = response.text.strip() or f"HTTP {response.status_code}"

    return f"HTTP {response.status_code}: {message}"

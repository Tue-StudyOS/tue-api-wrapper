import type { FeedbackIssueRequest } from "./feedback-types";

const FEEDBACK_REPOSITORY = "SebastianBoehler/tue-api-wrapper";

const sourceMarkers: Record<FeedbackIssueRequest["platform"], string> = {
  desktop: "tue-api-desktop-feedback"
};

const platformLabels: Record<FeedbackIssueRequest["platform"], string> = {
  desktop: "Desktop"
};

const categoryLabels: Record<FeedbackIssueRequest["category"], string> = {
  bug: "Bug",
  feature: "Feature",
  improvement: "Improvement",
  other: "Other"
};

export interface FeedbackIssueDraft {
  issueURL: string;
  title: string;
}

export function buildFeedbackIssueDraft(feedback: FeedbackIssueRequest): FeedbackIssueDraft {
  const title = `[${platformLabels[feedback.platform]} Feedback] ${categoryLabels[feedback.category]}: ${feedback.title}`;
  const params = new URLSearchParams({
    title,
    body: buildFeedbackIssueBody(feedback),
    labels: "feedback"
  });

  return {
    issueURL: `https://github.com/${FEEDBACK_REPOSITORY}/issues/new?${params.toString()}`,
    title
  };
}

function buildFeedbackIssueBody(feedback: FeedbackIssueRequest): string {
  const parts = [
    `<!-- source: ${sourceMarkers[feedback.platform]} -->`,
    `<!-- platform: ${feedback.platform} -->`,
    "## Summary",
    feedback.summary,
    "## Context",
    `- Category: ${categoryLabels[feedback.category]}`,
    `- Area: ${feedback.area || "Not specified"}`,
    `- App version: ${feedback.appVersion} (${feedback.buildNumber})`,
    `- OS version: ${feedback.systemVersion}`,
    `- Device: ${feedback.deviceModel}`,
    `- Submitted at: ${new Date().toISOString()}`
  ];

  if (feedback.reproductionSteps) {
    parts.push("## Reproduction Steps", feedback.reproductionSteps);
  }
  if (feedback.expectedBehavior) {
    parts.push("## Expected Behavior", feedback.expectedBehavior);
  }

  parts.push(
    "## Notes",
    "- Submitted from the Desktop feedback form.",
    "- Avoid posting personal data, credentials, or student records in follow-up comments."
  );

  return parts.join("\n\n");
}

import type { FeedbackIssueRequest } from "./feedback-types";

const FEEDBACK_REPOSITORY = "SebastianBoehler/tue-api-wrapper";
const FEEDBACK_TOKEN = import.meta.env.VITE_GITHUB_FEEDBACK_TOKEN?.trim() ?? "";

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

export interface FeedbackIssue {
  issueURL: string;
  title: string;
}

export function isFeedbackIssueCreationConfigured(): boolean {
  return FEEDBACK_TOKEN.length > 0;
}

export async function createFeedbackIssue(feedback: FeedbackIssueRequest): Promise<FeedbackIssue> {
  if (!isFeedbackIssueCreationConfigured()) {
    throw new Error("GitHub feedback is not configured for this build.");
  }

  const title = `[${platformLabels[feedback.platform]} Feedback] ${categoryLabels[feedback.category]}: ${feedback.title}`;
  const response = await fetch(`https://api.github.com/repos/${FEEDBACK_REPOSITORY}/issues`, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${FEEDBACK_TOKEN}`,
      "Content-Type": "application/json",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    body: JSON.stringify({
      title,
      body: buildFeedbackIssueBody(feedback),
      labels: ["feedback"]
    })
  });

  const body = await response.json().catch(() => null) as { html_url?: string; message?: string } | null;
  if (!response.ok || !body?.html_url) {
    throw new Error(body?.message ? `GitHub issue creation failed: ${body.message}` : "GitHub issue creation failed.");
  }

  return {
    issueURL: body.html_url,
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

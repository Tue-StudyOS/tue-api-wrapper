export type FeedbackIssuePlatform = "web";

export type FeedbackIssueCategory = "bug" | "feature" | "improvement" | "other";

export interface FeedbackIssueRequest {
  platform: FeedbackIssuePlatform;
  category: FeedbackIssueCategory;
  title: string;
  summary: string;
  area?: string | null;
  expectedBehavior?: string | null;
  reproductionSteps?: string | null;
  appVersion: string;
  buildNumber: string;
  systemVersion: string;
  deviceModel: string;
}

export interface FeedbackIssueResponse {
  issueNumber: number;
  issueURL: string;
  title: string;
}


import pkg from "../../package.json";
import { AppShell } from "../../components/app-shell";
import { FeedbackForm } from "../../components/feedback-form";
import { Card, CardContent } from "../../components/ui/card";
import { isFeedbackIssueCreationConfigured } from "../../lib/github-feedback";

export default async function FeedbackPage() {
  const buildNumber = (process.env.VERCEL_GIT_COMMIT_SHA || process.env.GITHUB_SHA || "dev").slice(0, 40);

  return (
    <AppShell title="Feedback">
      {isFeedbackIssueCreationConfigured() ? (
        <FeedbackForm appVersion={pkg.name} buildNumber={buildNumber} />
      ) : (
        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            Feedback issue creation is unavailable because this build has no GitHub feedback token.
          </CardContent>
        </Card>
      )}
    </AppShell>
  );
}

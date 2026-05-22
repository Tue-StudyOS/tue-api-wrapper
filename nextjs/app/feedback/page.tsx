import pkg from "../../package.json";
import { AppShell } from "../../components/app-shell";
import { FeedbackForm } from "../../components/feedback-form";
import { Card, CardContent } from "../../components/ui/card";
import { getFeedbackStatus } from "../../lib/portal-api";

export default async function FeedbackPage() {
  const buildNumber = (process.env.VERCEL_GIT_COMMIT_SHA || process.env.GITHUB_SHA || "dev").slice(0, 40);
  const feedbackStatus = await getFeedbackStatus().catch(() => ({
    enabled: false,
    repository: null,
    detail: "Feedback configuration status could not be loaded."
  }));

  return (
    <AppShell title="Feedback">
      {feedbackStatus.enabled ? (
        <FeedbackForm appVersion={pkg.name} buildNumber={buildNumber} />
      ) : (
        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            {feedbackStatus.detail}
          </CardContent>
        </Card>
      )}
    </AppShell>
  );
}

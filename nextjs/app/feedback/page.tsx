import pkg from "../../package.json";
import { AppShell } from "../../components/app-shell";
import { FeedbackForm } from "../../components/feedback-form";

export default function FeedbackPage() {
  const buildNumber = (process.env.VERCEL_GIT_COMMIT_SHA || process.env.GITHUB_SHA || "dev").slice(0, 40);
  return (
    <AppShell title="Feedback">
      <FeedbackForm appVersion={pkg.name} buildNumber={buildNumber} />
    </AppShell>
  );
}

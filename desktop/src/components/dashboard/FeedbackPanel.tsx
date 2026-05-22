import { useEffect, useMemo, useState } from "react";

import type { DesktopAppInfo } from "../../../shared/desktop-types";
import { submitFeedbackIssue } from "../../lib/api";
import type { FeedbackIssueCategory, FeedbackIssueResponse } from "../../lib/feedback-types";
import { PanelHeader } from "./DashboardPrimitives";

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "submitted"; response: FeedbackIssueResponse }
  | { status: "error"; message: string };

export function FeedbackPanel({ baseUrl }: { baseUrl: string | null }) {
  const [appInfo, setAppInfo] = useState<DesktopAppInfo | null>(null);
  const [category, setCategory] = useState<FeedbackIssueCategory>("bug");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [area, setArea] = useState("");
  const [expectedBehavior, setExpectedBehavior] = useState("");
  const [reproductionSteps, setReproductionSteps] = useState("");
  const [state, setState] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    window.desktop.getAppInfo().then((info) => {
      if (!cancelled) setAppInfo(info);
    }).catch(() => {
      if (!cancelled) setAppInfo(null);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const canSubmit = useMemo(() => {
    if (!baseUrl) return false;
    if (state.status === "submitting") return false;
    return title.trim().length >= 4 && summary.trim().length >= 10;
  }, [baseUrl, state.status, summary, title]);

  async function onSubmit(): Promise<void> {
    if (!baseUrl) return;
    setState({ status: "submitting" });
    try {
      const payload = {
        platform: "desktop",
        category,
        title: title.trim(),
        summary: summary.trim(),
        area: area.trim() ? area.trim() : null,
        expectedBehavior: expectedBehavior.trim() ? expectedBehavior.trim() : null,
        reproductionSteps: reproductionSteps.trim() ? reproductionSteps.trim() : null,
        appVersion: appInfo?.appVersion ?? "unknown",
        buildNumber: appInfo?.buildNumber ?? "unknown",
        systemVersion: appInfo?.systemVersion ?? "unknown",
        deviceModel: appInfo?.deviceModel ?? "unknown"
      } as const;
      const response = await submitFeedbackIssue(baseUrl, payload);
      setState({ status: "submitted", response });
      setTitle("");
      setSummary("");
      setArea("");
      setExpectedBehavior("");
      setReproductionSteps("");
    } catch (error) {
      setState({ status: "error", message: error instanceof Error ? error.message : "Feedback submission failed." });
    }
  }

  return (
    <article className="panel">
      <PanelHeader title="Feedback" meta={baseUrl ? "Connected" : "Unavailable"} />

      {!baseUrl ? (
        <p className="muted">Connect the local backend to submit feedback.</p>
      ) : (
        <div className="stack-list">
          <label className="field">
            <span>Category</span>
            <select value={category} onChange={(event) => setCategory(event.target.value as FeedbackIssueCategory)}>
              <option value="bug">Bug</option>
              <option value="feature">Feature</option>
              <option value="improvement">Improvement</option>
              <option value="other">Other</option>
            </select>
          </label>
          <p className="muted">Creates a GitHub issue via the local Python backend.</p>

          <label className="field">
            <span>Title</span>
            <input placeholder="Short summary" value={title} onChange={(event) => setTitle(event.target.value)} type="text" />
          </label>

          <label className="field">
            <span>Summary</span>
            <textarea
              placeholder="What happened and what should happen instead?"
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              rows={5}
            />
          </label>

          <label className="field">
            <span>Area (optional)</span>
            <input placeholder="e.g. Mail, Timetable, Discovery" value={area} onChange={(event) => setArea(event.target.value)} type="text" />
          </label>

          <label className="field">
            <span>Reproduction steps (optional)</span>
            <textarea
              placeholder="How can it be reproduced?"
              value={reproductionSteps}
              onChange={(event) => setReproductionSteps(event.target.value)}
              rows={4}
            />
          </label>

          <label className="field">
            <span>Expected behavior (optional)</span>
            <textarea
              placeholder="What should the app do?"
              value={expectedBehavior}
              onChange={(event) => setExpectedBehavior(event.target.value)}
              rows={3}
            />
          </label>

          {state.status === "error" ? <p className="muted">Error: {state.message}</p> : null}
          {state.status === "submitted" ? (
            <div className="stack-row compact-row">
              <div>
                <strong>Submitted</strong>
                <span>Issue #{state.response.issueNumber}: {state.response.title}</span>
              </div>
              <button className="secondary-button compact-button" onClick={() => void window.desktop.openExternal(state.response.issueURL)} type="button">
                Open
              </button>
            </div>
          ) : null}

          <div className="settings-actions">
            <button className="secondary-button" disabled={!canSubmit} onClick={() => void onSubmit()} type="button">
              {state.status === "submitting" ? "Submitting..." : "Submit feedback"}
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

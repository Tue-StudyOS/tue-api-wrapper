"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { FeedbackIssueCategory, FeedbackIssueRequest, FeedbackIssueResponse } from "@/lib/feedback-types";

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "submitted"; response: FeedbackIssueResponse }
  | { status: "error"; message: string };

export function FeedbackForm({
  appVersion,
  buildNumber
}: {
  appVersion: string;
  buildNumber: string;
}) {
  const [category, setCategory] = useState<FeedbackIssueCategory>("bug");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [area, setArea] = useState("");
  const [expectedBehavior, setExpectedBehavior] = useState("");
  const [reproductionSteps, setReproductionSteps] = useState("");
  const [state, setState] = useState<SubmitState>({ status: "idle" });

  const canSubmit = useMemo(() => {
    if (state.status === "submitting") return false;
    return title.trim().length >= 4 && summary.trim().length >= 10;
  }, [state.status, summary, title]);

  async function submit(): Promise<void> {
    setState({ status: "submitting" });
    try {
      const systemVersion = (navigator.userAgent || "unknown").slice(0, 60);
      const deviceModel = (navigator.platform || "unknown").slice(0, 60);
      const payload: FeedbackIssueRequest = {
        platform: "web",
        category,
        title: title.trim(),
        summary: summary.trim(),
        area: area.trim() ? area.trim() : null,
        expectedBehavior: expectedBehavior.trim() ? expectedBehavior.trim() : null,
        reproductionSteps: reproductionSteps.trim() ? reproductionSteps.trim() : null,
        appVersion,
        buildNumber,
        systemVersion,
        deviceModel
      };

      const response = await fetch("/api/feedback/issues", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(detail || `Backend returned HTTP ${response.status}.`);
      }

      const json = (await response.json()) as FeedbackIssueResponse;
      setState({ status: "submitted", response: json });
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
    <Card>
      <CardContent className="pt-6 flex flex-col gap-4">
        <div className="text-sm text-muted-foreground">
          Submits a GitHub issue via the Python backend. The backend needs `GITHUB_FEEDBACK_TOKEN` configured.
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Category</label>
          <select
            className="h-9 w-full rounded-lg border border-transparent bg-input/50 px-3 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            value={category}
            onChange={(event) => setCategory(event.target.value as FeedbackIssueCategory)}
          >
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
            <option value="improvement">Improvement</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Title</label>
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Short summary" />
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Summary</label>
          <textarea
            className="min-h-28 w-full rounded-lg border border-transparent bg-input/50 px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            value={summary}
            onChange={(event) => setSummary(event.target.value)}
            placeholder="What happened and what should happen instead?"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Area (optional)</label>
          <Input value={area} onChange={(event) => setArea(event.target.value)} placeholder="e.g. Timetable, Mail, Discovery" />
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Reproduction steps (optional)</label>
          <textarea
            className="min-h-24 w-full rounded-lg border border-transparent bg-input/50 px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            value={reproductionSteps}
            onChange={(event) => setReproductionSteps(event.target.value)}
            placeholder="How can it be reproduced?"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm font-medium">Expected behavior (optional)</label>
          <textarea
            className="min-h-20 w-full rounded-lg border border-transparent bg-input/50 px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            value={expectedBehavior}
            onChange={(event) => setExpectedBehavior(event.target.value)}
            placeholder="What should happen?"
          />
        </div>

        {state.status === "error" ? (
          <div className="text-sm text-destructive whitespace-pre-wrap">{state.message}</div>
        ) : null}

        {state.status === "submitted" ? (
          <div className="flex items-center justify-between gap-3 rounded-lg bg-muted/30 px-4 py-3">
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">Issue #{state.response.issueNumber}</div>
              <div className="text-xs text-muted-foreground truncate">{state.response.title}</div>
            </div>
            <Button asChild variant="secondary" size="sm">
              <a href={state.response.issueURL} target="_blank" rel="noreferrer">
                Open
              </a>
            </Button>
          </div>
        ) : null}

        <Button disabled={!canSubmit} onClick={() => void submit()}>
          {state.status === "submitting" ? "Submitting..." : "Submit feedback"}
        </Button>
      </CardContent>
    </Card>
  );
}


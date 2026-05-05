import { useEffect, useMemo, useState } from "react";

import { fetchExamReports } from "../../lib/api";
import type { DashboardDocumentReport, DashboardEnrollmentEntry, DashboardExamItem, DashboardStudyPlannerModule } from "../../lib/dashboard-types";
import { formatCredits } from "../../lib/format";
import { EmptyState, PanelHeader } from "./DashboardPrimitives";
import type { DashboardPageProps } from "./types";

export function StudyPage({ data, state }: DashboardPageProps) {
  const [examReports, setExamReports] = useState<DashboardDocumentReport[]>([]);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const passedExams = useMemo(() => (data?.exams ?? []).filter(isPassedExam), [data?.exams]);
  const plannerModules = useMemo(() => progressModules(data?.study.planner?.modules ?? []), [data?.study.planner?.modules]);
  const enrollments = data?.study.enrollments ?? [];
  const studyNote = data?.study.currentSemesterCreditError
    ?? (data?.study.currentSemesterCreditUnresolved?.length
      ? `${data.study.currentSemesterCreditUnresolved.length} timetable entries have no CP value.`
      : "Live Alma values are reflected in the saved semester total.");

  useEffect(() => {
    if (!state.backendUrl) {
      setExamReports([]);
      setReportLoading(false);
      return;
    }
    let cancelled = false;
    setExamReports([]);
    setReportError(null);
    setReportLoading(true);
    void fetchExamReports(state.backendUrl)
      .then((reports) => {
        if (!cancelled) setExamReports(reports);
      })
      .catch((error) => {
        if (!cancelled) setReportError(error instanceof Error ? error.message : "Could not load exam reports.");
      })
      .finally(() => {
        if (!cancelled) setReportLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [state.backendUrl]);

  function openExamReport(report: DashboardDocumentReport) {
    if (!state.backendUrl) return;
    setReportError(null);
    const params = new URLSearchParams({ trigger_name: report.trigger_name });
    void window.desktop.openExternal(`${state.backendUrl}/api/alma/exams/report?${params}`).catch((error) => {
      setReportError(error instanceof Error ? error.message : "Could not open Alma report.");
    });
  }

  return (
    <div className="content-grid">
      <article className="panel">
        <PanelHeader title="Study progress" meta={formatCredits(data?.study.currentSemesterCredits)} />
        <div className="stack-list">
          <div className="stack-row compact-row">
            <div>
              <strong>Saved semester credits</strong>
              <span>{studyNote}</span>
            </div>
            <span>{formatCredits(data?.study.currentSemesterCredits)}</span>
          </div>
          <div className="stack-row compact-row">
            <div>
              <strong>Tracked credits</strong>
              <span>{data?.study.selectedTerm ?? "No selected term"}</span>
            </div>
            <span>{data?.study.trackedCredits ?? 0} CP</span>
          </div>
          <div className="stack-row compact-row">
            <div>
              <strong>Passed exams</strong>
              <span>Derived from the Alma exam overview</span>
            </div>
            <span>{data?.study.passedExamCount ?? 0}</span>
          </div>
        </div>
      </article>

      <article className="panel">
        <PanelHeader title="Passed exams" meta={`${passedExams.length} passed`} />
        <div className="stack-list">
          {passedExams.map((exam) => (
            <div key={`${exam.number}-${exam.title}-${exam.grade}-${exam.status}`} className="stack-row compact-row">
              <div>
                <strong>{exam.title}</strong>
                <span>{examMeta(exam)}</span>
              </div>
              <span>{exam.grade || exam.status || "Passed"}</span>
            </div>
          ))}
          {passedExams.length === 0 ? <EmptyState>No passed exam rows returned by Alma.</EmptyState> : null}
        </div>
      </article>

      <article className="panel">
        <div className="section-heading study-module-heading">
          <div>
            <h3>Module areas</h3>
            <span>{plannerSubtitle(data?.study.planner?.title)}</span>
          </div>
        </div>
        <div className="stack-list">
          {plannerModules.map((module) => (
            <div key={`${module.number}-${module.title}`} className="stack-row compact-row">
              <div>
                <strong>{moduleAreaTitle(module.title)}</strong>
                <span>{module.number ?? "No module code"}</span>
                {typeof module.progress_percent === "number" ? (
                  <div className="progress-track" aria-label={`${moduleAreaTitle(module.title)} progress`}>
                    <span style={{ width: `${module.progress_percent}%` }} />
                  </div>
                ) : null}
              </div>
              <span>{module.credits_summary ?? "No CP"}</span>
            </div>
          ))}
          {data?.study.plannerError ? <p className="inline-error">{data.study.plannerError}</p> : null}
          {!plannerModules.length && !data?.study.plannerError ? (
            <EmptyState>No Alma planner module areas returned.</EmptyState>
          ) : null}
        </div>
      </article>

      <article className="panel">
        <PanelHeader title="Enrollments" meta={`${enrollments.length} rows`} />
        <div className="stack-list">
          {enrollments.slice(0, 8).map((entry) => (
            <div key={`${entry.number}-${entry.title}-${entry.status}`} className="stack-row compact-row">
              <div>
                <strong>{entry.title}</strong>
                <span>{enrollmentMeta(entry)}</span>
              </div>
              <span>{entry.status ?? "No status"}</span>
            </div>
          ))}
          {enrollments.length === 0 ? <EmptyState>No Alma enrollment rows returned.</EmptyState> : null}
        </div>
      </article>

      <article className="panel wide-panel">
        <PanelHeader title="Documents" meta={reportLoading ? "Loading reports..." : `${examReports.length} exam reports`} />
        <div className="action-list">
          {state.backendUrl && data?.documents.currentDownloadUrl ? (
            <button
              className="secondary-button full-width"
              onClick={() => void window.desktop.openExternal(`${state.backendUrl}${data.documents.currentDownloadUrl}`)}
              type="button"
            >
              Open current Alma PDF
            </button>
          ) : null}
          {examReports.map((report) => (
            <button
              key={report.trigger_name}
              className="stack-row compact-row"
              disabled={!state.backendUrl}
              onClick={() => openExamReport(report)}
              type="button"
            >
              <div>
                <strong>{report.label}</strong>
                <span>Generated from Alma exam reports</span>
              </div>
              <span>Open PDF</span>
            </button>
          ))}
          {reportLoading ? <EmptyState>Loading Alma exam reports...</EmptyState> : null}
          {reportError ? <p className="inline-error">{reportError}</p> : null}
          {!reportLoading && !examReports.length && !reportError ? (
            <EmptyState>No Alma exam report actions returned.</EmptyState>
          ) : null}
        </div>
      </article>
    </div>
  );
}

function isPassedExam(exam: DashboardExamItem): boolean {
  const status = (exam.status ?? "").trim().toUpperCase();
  const grade = (exam.grade ?? "").trim();
  return ["BE", "PASSED", "BESTANDEN"].includes(status) || Boolean(grade && !["-", "5,0"].includes(grade));
}

function examMeta(exam: DashboardExamItem): string {
  return [exam.number, exam.cp, exam.status].filter(Boolean).join(" · ") || "No structured label available";
}

function progressModules(modules: DashboardStudyPlannerModule[]): DashboardStudyPlannerModule[] {
  return modules.filter((module) => module.credits_summary || module.credits_required || module.credits_earned);
}

function enrollmentMeta(entry: DashboardEnrollmentEntry): string {
  return [entry.number, entry.event_type, entry.semester, summarizeSchedule(entry.schedule_text)]
    .filter(Boolean)
    .join(" · ");
}

function plannerSubtitle(title?: string | null): string {
  const cleaned = title
    ?.replace(/^Studienplaner\s+/i, "")
    .replace(/\s+-\s+Eberhard Karls Universität Tübingen$/i, "")
    .replace(/\s*\/\s*/g, ", ")
    .trim();
  return cleaned || "Alma planner";
}

function moduleAreaTitle(title: string): string {
  return title.replace(/^Studienbereich\s+/i, "").trim() || title;
}

function summarizeSchedule(text?: string | null): string | null {
  if (!text) return null;
  const cleaned = cleanEnrollmentText(text);
  const recurring = [...cleaned.matchAll(/jeden\s+([A-Za-zÄÖÜäöüß]+).*?\bvon\s+(\d{2}:\d{2})\s+bis\s+(\d{2}:\d{2})/g)]
    .slice(0, 2)
    .map((match) => `${match[1]} ${match[2]}-${match[3]}`);
  if (recurring.length) return recurring.join(", ");

  const single = cleaned.match(/([A-ZÄÖÜ][A-Za-zÄÖÜäöüß]+),\s*\d{2}\.\d{2}\.\d{2}\s+von\s+(\d{2}:\d{2})\s+bis\s+(\d{2}:\d{2})/);
  if (single) return `${single[1]} ${single[2]}-${single[3]}`;

  return cleaned.length > 120 ? `${cleaned.slice(0, 117).trim()}...` : cleaned;
}

function cleanEnrollmentText(text: string): string {
  return text
    .replace(/\b(Status|Aktionen|Details anzeigen|Informationen zu Belegzeiträumen)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

import type { DashboardPayload } from "../../src/types.js";
import { escapeHtml, formatCredits, formatDate } from "./widget-format.js";
import { renderAgendaRow, renderFallbackRow, renderDetailButton, buildExamDetail, buildTaskDetail, buildMembershipDetail, buildTalkDetail } from "./widget-rows.js";

export function renderOverview(dashboard: DashboardPayload): string {
  const metrics = dashboard.metrics
    .map(
      (metric) => `
        <article class="metric-card">
          <span>${escapeHtml(metric.label)}</span>
          <strong>${metric.value}</strong>
        </article>
      `
    )
    .join("");

  const agenda = dashboard.agenda.items
    .slice(0, 5)
    .map((item) => renderAgendaRow(item, "teal"))
    .join("") || renderFallbackRow("No upcoming Alma events found.");

  const documents = dashboard.documents.reports
    .slice(0, 4)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.label)}</strong>

          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No Alma document jobs available.");

  const exams = dashboard.exams
    .slice(0, 4)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.number ?? item.status ?? "Status pending")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.grade ?? item.cp ?? item.status ?? "-")}</span>
            ${renderDetailButton(buildExamDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No Alma exam rows found.");

  const tasks = dashboard.ilias.tasks
    .slice(0, 5)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.item_type ?? "Task")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.end ?? item.start ?? "-")}</span>
            ${renderDetailButton(buildTaskDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No open ILIAS tasks found.");

  const memberships = dashboard.ilias.memberships
    .slice(0, 4)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.description ?? item.properties[0] ?? item.kind ?? "Learning space")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.kind ?? "Open")}</span>
            ${renderDetailButton(buildMembershipDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No current ILIAS memberships found.");

  const talks = dashboard.talks.available
    ? dashboard.talks.items
      .slice(0, 4)
      .map(
        (item) => `
          <div class="widget-row compact">
            <div>
              <strong>${escapeHtml(item.title)}</strong>
              <p>${escapeHtml(item.speaker_name ?? item.location ?? "Speaker pending")}</p>
            </div>
            <div class="widget-row-actions">
              <time>${escapeHtml(formatDate(item.timestamp))}</time>
              ${renderDetailButton(buildTalkDetail(item))}
            </div>
          </div>
        `
      )
      .join("") || renderFallbackRow("No upcoming talks found.")
    : renderFallbackRow(dashboard.talks.error ?? "Talks unavailable.");

  const studySummary = `
    <div class="widget-summary">
      <div>
        <span>Saved semester</span>
        <strong>${formatCredits(dashboard.study.currentSemesterCredits)}</strong>
      </div>
      <div>
        <span>Tracked credits</span>
        <strong>${dashboard.study.trackedCredits}</strong>
      </div>
      <div>
        <span>Passed exams</span>
        <strong>${dashboard.study.passedExamCount}</strong>
      </div>
      <div>
        <span>Term</span>
        <strong>${escapeHtml(dashboard.study.selectedTerm ?? dashboard.termLabel)}</strong>
      </div>
    </div>
  `;

  const quickActions = [
    "What should I focus on this week based on my schedule, tasks, and grades?",
    "List my next lectures and meetings.",
    "Summarize my current grades and credits.",
    "Suggest courses for next semester based on my current study progress."
  ]
    .map(
      (prompt) => `
        <button class="widget-button ghost" data-follow-up="${escapeHtml(prompt)}">
          ${escapeHtml(prompt)}
        </button>
      `
    )
    .join("");

  return `
    <section class="metric-row">${metrics}</section>

    <section class="widget-grid">
      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Agenda</p>
            <h2>Upcoming events</h2>
          </div>
          <button class="widget-button ghost small" data-action="set-panel" data-panel="schedule">Focus</button>
        </div>
        <div class="widget-list">${agenda}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Tasks</p>
            <h2>Open ILIAS work</h2>
          </div>
          <button class="widget-button ghost small" data-action="set-panel" data-panel="tasks">Focus</button>
        </div>
        <div class="widget-list">${tasks}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Progress</p>
            <h2>Study status</h2>
          </div>
          <button class="widget-button ghost small" data-action="set-panel" data-panel="grades">Focus</button>
        </div>
        ${studySummary}
        <div class="widget-list">${exams}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Spaces</p>
            <h2>Learning spaces</h2>
          </div>
          <button class="widget-button ghost small" data-action="set-panel" data-panel="spaces">Focus</button>
        </div>
        <div class="widget-list">${memberships}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Documents</p>
            <h2>Study service</h2>
          </div>
          <button class="widget-button" data-follow-up="List the study-service document options from Alma.">Ask</button>
        </div>
        <div class="widget-list">${documents}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Talks</p>
            <h2>Upcoming talks</h2>
          </div>
          <button class="widget-button ghost" data-follow-up="Summarize the next public talks from my study dashboard.">Ask</button>
        </div>
        <div class="widget-list">${talks}</div>
      </article>

      <article class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Assistant</p>
            <h2>Ask next</h2>
          </div>
          <button class="widget-button ghost small" data-action="set-panel" data-panel="courses">Courses</button>
        </div>
        <div class="widget-actions">${quickActions}</div>
      </article>
    </section>
  `;
}

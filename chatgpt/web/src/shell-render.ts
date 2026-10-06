import type { PanelName } from "./widget-types.js";
import { state } from "./widget-state.js";
import { getDashboard, getRenderedModuleDetail } from "./dashboard-data.js";
import { escapeHtml } from "./widget-format.js";
import { renderModuleDetailTemplate } from "./module-detail-render.js";
import { renderInlineOverview } from "./inline-overview.js";

export function renderError(message: string): string {
  return `
    <div class="widget-empty">
      <p class="widget-kicker" role="alert">Request failed</p>
      <h1>Study data unavailable</h1>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

export { notifyRenderedHeight } from "./widget-height.js";

export function renderDetailTemplate(): string {
  const moduleDetail = getRenderedModuleDetail();
  if (moduleDetail) {
    return renderModuleDetailTemplate(moduleDetail, escapeHtml);
  }

  const detail = state.detailModal;
  if (!detail) {
    return `
      <div class="widget-empty">
        <p class="widget-kicker">Details</p>
        <h1>No detail selected</h1>
        <p>Choose an item from the dashboard first.</p>
      </div>
    `;
  }

  return `
    <div class="widget-stack widget-modal-stack">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">Detail</p>
          <h1>${escapeHtml(detail.title)}</h1>
          ${detail.subtitle ? `<p>${escapeHtml(detail.subtitle)}</p>` : ""}
        </div>
        <button class="widget-button ghost" data-action="close-modal">Close</button>
      </header>
      <article class="widget-card widget-card-wide">
        <div class="widget-list">
          ${detail.lines.map((line) => `<div class="widget-row compact"><p>${escapeHtml(line)}</p></div>`).join("")}
        </div>
        ${
          detail.href
            ? `
              <div class="widget-modal-actions">
                <button class="widget-button" data-action="open-external" data-href="${escapeHtml(detail.href)}">
                  ${escapeHtml(detail.hrefLabel ?? "Open source")}
                </button>
              </div>
            `
            : ""
        }
      </article>
    </div>
  `;
}

export function renderAppShell(content: string): string {
  const dashboard = getDashboard();
  const panelTabs: Array<{ key: PanelName; label: string }> = [
    { key: "overview", label: "Overview" },
    { key: "schedule", label: "Schedule" },
    { key: "tasks", label: "Tasks" },
    { key: "grades", label: "Grades" },
    { key: "spaces", label: "Spaces" },
    { key: "courses", label: "Courses" }
  ];

  const controls = `<div class="widget-card-actions">
          <button class="widget-button ghost small" data-action="toggle-expand" aria-pressed="${state.expanded}">
            ${state.expanded ? "Collapse" : "Open dashboard"}
          </button>
          <button class="widget-button ghost small" data-follow-up="Summarize the most urgent things in my study dashboard.">Summarize</button>
        </div>`;
  return `
    <div class="widget-stack widget-shell${state.expanded ? " is-expanded" : ""}">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">${escapeHtml(dashboard?.termLabel ?? "Study Hub")}</p>
          <h1>${escapeHtml(dashboard?.hero.title ?? "Study Hub")}</h1>
          <p>${escapeHtml(dashboard?.hero.subtitle ?? "Your schedule, tasks, and study progress.")}</p>
        </div>
        ${state.expanded ? controls : ""}
      </header>

      ${state.expanded ? `<nav class="widget-tabs" aria-label="Study dashboard panels">
        ${panelTabs
          .map(
            (tab) => `
              <button
                class="widget-tab${state.activePanel === tab.key ? " is-active" : ""}"
                data-action="set-panel"
                aria-pressed="${state.activePanel === tab.key}"
                data-panel="${tab.key}"
              >
                ${escapeHtml(tab.label)}
              </button>
            `
          )
          .join("")}
      </nav>` : ""}

      <main class="widget-scroll" tabindex="0">
        ${!state.expanded && dashboard ? `${state.panelError ? `<p role="alert">${escapeHtml(state.panelError)}</p>` : ""}${renderInlineOverview(dashboard)}` : content}

        ${
          state.inlineDetailOpen && state.detailModal
            ? `
              <section class="widget-card widget-card-wide">
                <div class="widget-card-header">
                  <div>
                    <p class="widget-kicker">Inline detail</p>
                    <h2>${escapeHtml(state.detailModal.title)}</h2>
                  </div>
                  <button class="widget-button ghost small" data-action="dismiss-inline-detail">Close</button>
                </div>
                <div class="widget-list">
                  ${state.detailModal.lines.map((line) => `<div class="widget-row compact"><p>${escapeHtml(line)}</p></div>`).join("")}
                </div>
              </section>
            `
            : ""
        }
      </main>
      ${state.expanded ? "" : controls}

      ${
        dashboard?.generatedAt
          ? `
            <footer class="widget-footer-meta">
              Last updated ${escapeHtml(
                new Intl.DateTimeFormat("de-DE", {
                  timeZone: "Europe/Berlin",
                  dateStyle: "medium",
                  timeStyle: "short"
                }).format(new Date(dashboard.generatedAt))
              )}
            </footer>
          `
          : ""
      }
    </div>
  `;
}

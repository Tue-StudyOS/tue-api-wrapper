import type { DashboardPayload } from "../../src/types.js";
import { escapeHtml, formatDate } from "./widget-format.js";

export function renderInlineOverview(dashboard: DashboardPayload): string {
  const events = dashboard.agenda.items.slice(0, 2).map((item) => `
    <div class="widget-row compact"><div><strong>${escapeHtml(item.summary)}</strong>
      <p>${escapeHtml(formatDate(item.start))}${item.location ? ` · ${escapeHtml(item.location)}` : ""}</p>
    </div></div>`).join("");
  const tasks = dashboard.ilias.tasks.slice(0, 2).map((item) => `
    <div class="widget-row compact"><div><strong>${escapeHtml(item.title)}</strong>
      ${item.end ? `<p>Due ${escapeHtml(formatDate(item.end))}</p>` : ""}
    </div></div>`).join("");
  return `<section class="widget-inline-summary" aria-label="Study overview">
    <div class="widget-summary">${dashboard.metrics.map((metric) => `
      <div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(String(metric.value))}</strong></div>
    `).join("")}</div>
    <div class="widget-inline-sections">
      <section><h2>Next events</h2><div class="widget-list">${events || '<p>No upcoming events found.</p>'}</div></section>
      <section><h2>Open tasks</h2><div class="widget-list">${tasks || '<p>No open tasks found.</p>'}</div></section>
    </div></section>`;
}

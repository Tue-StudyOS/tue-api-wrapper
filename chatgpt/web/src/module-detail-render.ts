import "./module-detail.css";

import type { ModuleDetail } from "../../src/types.js";

type EscapeHtml = (value: string | null | undefined) => string;

export function isModuleDetail(value: unknown): value is ModuleDetail {
  return Boolean(
    value &&
      typeof value === "object" &&
      "source_url" in value &&
      "sections" in value &&
      "module_study_program_tables" in value
  );
}

export function renderModuleDetailTemplate(detail: ModuleDetail, escapeHtml: EscapeHtml): string {
  return `
    <div class="widget-stack widget-modal-stack">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">${escapeHtml(detail.number ?? "Alma detail")}</p>
          <h1>${escapeHtml(detail.title)}</h1>
          ${detail.active_tab ? `<p>${escapeHtml(`Active tab: ${detail.active_tab}`)}</p>` : ""}
        </div>
        <button class="widget-button ghost" data-action="close-modal">Close</button>
      </header>
      ${renderAvailableTabs(detail, escapeHtml)}
      ${renderModuleDetailSections(detail, escapeHtml)}
      ${renderModuleStudyProgramTables(detail, escapeHtml)}
      ${renderSourceAction(detail, escapeHtml)}
    </div>
  `;
}

function renderAvailableTabs(detail: ModuleDetail, escapeHtml: EscapeHtml): string {
  if (!detail.available_tabs.length) {
    return "";
  }
  return `
    <section class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Tabs</p>
          <h2>Available Alma sections</h2>
        </div>
      </div>
      <div class="widget-tags">
        ${detail.available_tabs.map((tab) => `<span>${escapeHtml(tab)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderModuleDetailSections(detail: ModuleDetail, escapeHtml: EscapeHtml): string {
  return detail.sections
    .map(
      (section) => `
        <section class="widget-card widget-card-wide">
          <div class="widget-card-header">
            <div>
              <p class="widget-kicker">${escapeHtml(section.title)}</p>
              <h2>${escapeHtml(section.title)}</h2>
            </div>
          </div>
          <div class="widget-list">
            ${section.fields
              .map(
                (field) => `
                  <div class="widget-row compact">
                    <strong>${escapeHtml(field.label)}</strong>
                    <p>${escapeHtml(field.value)}</p>
                  </div>
                `
              )
              .join("")}
          </div>
        </section>
      `
    )
    .join("");
}

function renderModuleStudyProgramTables(detail: ModuleDetail, escapeHtml: EscapeHtml): string {
  return detail.module_study_program_tables.map((table) => renderDetailTable(table, escapeHtml)).join("");
}

function renderDetailTable(
  table: ModuleDetail["module_study_program_tables"][number],
  escapeHtml: EscapeHtml,
): string {
  const columnCount = Math.max(1, table.headers.length, ...table.rows.map((row) => row.length));
  const columnIndexes = Array.from({ length: columnCount }, (_, index) => index);
  return `
    <section class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Module / Studiengänge</p>
          <h2>${escapeHtml(table.title)}</h2>
        </div>
      </div>
      <div class="widget-table-wrap">
        <table class="widget-table">
          <thead>
            <tr>${columnIndexes.map((index) => `<th>${escapeHtml(table.headers[index] ?? `Spalte ${index + 1}`)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${table.rows
              .map(
                (row) => `
                  <tr>${columnIndexes.map((index) => `<td>${escapeHtml(row[index] ?? "")}</td>`).join("")}</tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderSourceAction(detail: ModuleDetail, escapeHtml: EscapeHtml): string {
  const href = detail.permalink ?? detail.source_url;
  return href
    ? `
      <section class="widget-card widget-source-card">
        <div class="widget-card-actions">
          <button class="widget-button" data-action="open-external" data-href="${escapeHtml(href)}">
            Open Alma source
          </button>
        </div>
      </section>
    `
    : "";
}

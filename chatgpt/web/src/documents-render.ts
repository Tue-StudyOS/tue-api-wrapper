import type { DocumentsSummaryPayload } from "../../src/types.js";

import { escapeHtml } from "./widget-format.js";

function renderStatusRow(label: string, value: string | null | undefined): string {
  if (!value) {
    return "";
  }
  return `
    <div class="widget-row compact">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `;
}

function renderTabs(documents: DocumentsSummaryPayload): string {
  if (!documents.tabs.length) {
    return "";
  }
  return `
    <div class="widget-tags" aria-label="Alma page sections">
      ${documents.tabs
        .map(
          (tab) => `
            <span>
              ${escapeHtml(tab.label)}
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPageState(documents: DocumentsSummaryPayload): string {
  const statusRows = [
    renderStatusRow("Status", documents.bannerText),
    renderStatusRow("Person", documents.personName),
    renderStatusRow("Active tab", documents.activeTabLabel),
  ].join("");
  const tabs = renderTabs(documents);

  if (!statusRows && !tabs) {
    return "";
  }

  return `
    <section class="widget-card">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Alma page state</p>
          <h2>Returned successfully</h2>
        </div>
      </div>
      <div class="widget-list">
        ${statusRows}
        ${tabs}
      </div>
    </section>
  `;
}

function renderCurrentDownload(documents: DocumentsSummaryPayload): string {
  if (documents.currentDownloadUrl) {
    return `
      <section class="widget-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Live download</p>
            <h2>Current Alma PDF</h2>
          </div>
          <a href="${escapeHtml(documents.currentDownloadUrl)}" target="_blank" rel="noreferrer">
            Download
          </a>
        </div>
      </section>
    `;
  }

  if (!documents.currentDownloadAvailable) {
    return "";
  }

  return `
    <section class="widget-card">
      <p class="widget-kicker">Live download</p>
      <h2>PDF marked available</h2>
      <p>Alma reports a current PDF, but no direct download URL was returned.</p>
    </section>
  `;
}

function renderOutputRequests(documents: DocumentsSummaryPayload): string {
  if (!documents.outputRequests.length) {
    return "";
  }
  return `
    <section class="widget-card">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Output requests</p>
          <h2>Request groups</h2>
        </div>
      </div>
      <div class="widget-list">
        ${documents.outputRequests
          .map(
            (item) => `
              <div class="widget-row compact">
                <div>
                  <strong>${escapeHtml(item.label)}</strong>
                  <p>${escapeHtml(item.message ?? item.trigger_name)}</p>
                </div>
                ${item.count === null ? "" : `<span>${escapeHtml(String(item.count))}</span>`}
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderReports(documents: DocumentsSummaryPayload): string {
  if (!documents.reports.length) {
    return "";
  }
  return `
    <section class="widget-card">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Report jobs</p>
          <h2>Available exports</h2>
        </div>
      </div>
      <div class="widget-list">
        ${documents.reports
          .map(
            (item) => `
              <div class="widget-row compact">
                <strong>${escapeHtml(item.label)}</strong>

              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderNoExports(documents: DocumentsSummaryPayload): string {
  const tabContext = documents.tabs.length
    ? ` Alma returned ${documents.tabs.length} study-service tabs, but none exposed a report job, output request, or current PDF download.`
    : "";

  return `
    <section class="widget-card">
      <p class="widget-kicker">No exports available</p>
      <h2>No report jobs or PDF downloads were returned</h2>
      <p>The study-service page loaded successfully for the current account.${tabContext}</p>
    </section>
  `;
}

export function renderDocuments(documents: DocumentsSummaryPayload): string {
  const hasExports =
    documents.reports.length > 0 ||
    documents.outputRequests.length > 0 ||
    documents.currentDownloadAvailable ||
    Boolean(documents.currentDownloadUrl);

  return `
    <div class="widget-stack widget-modal-stack">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">Documents</p>
          <h1>Study-service exports</h1>
          <p>View your available certificates, report options, and current PDF.</p>
        </div>
      </header>
      ${renderPageState(documents)}
      ${renderCurrentDownload(documents)}
      ${renderOutputRequests(documents)}
      ${renderReports(documents)}
      ${hasExports ? "" : renderNoExports(documents)}
    </div>
  `;
}

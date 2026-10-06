import { notifyRenderedHeight as notifyActionHeight } from "./widget-height.js";
import "./action-confirmation.css";
import { callHostTool } from "./widget-bridge.js";

import type { CriticalActionPublicIntent, CriticalActionResult, CriticalActionView } from "../../src/types/actions.js";

type EscapeHtml = (value: string | null | undefined) => string;

interface ActionToolResult {
  status: "completed";
  intent: CriticalActionPublicIntent;
  result: CriticalActionResult;
}

interface ActionMetadata {
  confirmationToken?: string;
}

interface ActionOpenAIHost {
  callTool?: <T = unknown>(name: string, args?: Record<string, unknown>) => Promise<{
    structuredContent?: T;
    content?: Array<{ type: string; text?: string }>;
    _meta?: Record<string, unknown>;
  }>;
  requestClose?: () => Promise<void>;
  notifyIntrinsicHeight?: (height?: number) => void;
}

type ActionRenderResult = CriticalActionView | ActionToolResult | { error: string } | { view: "error"; message: string } | null;

let currentResult: ActionRenderResult = null;
let confirmationToken = "";
let isSubmitting = false;

function host(): ActionOpenAIHost | undefined {
  return (window as typeof window & { openai?: ActionOpenAIHost }).openai;
}

export function isCriticalActionView(value: unknown): value is CriticalActionView {
  return Boolean(value && typeof value === "object" && "view" in value && (value as { view?: unknown }).view === "critical-action");
}

export function renderActionTemplate(
  root: HTMLElement,
  result: ActionRenderResult,
  metadata: ActionMetadata | undefined,
  escapeHtml: EscapeHtml,
) {
  currentResult = result;
  confirmationToken = metadata?.confirmationToken ?? "";

  if (isActionToolResult(result)) {
    root.innerHTML = renderCompleted(result, escapeHtml);
  } else if (isCriticalActionView(result)) {
    root.innerHTML = renderConfirmation(result.intent, escapeHtml);
  } else if (result && "error" in result) {
    root.innerHTML = renderError(result.error, escapeHtml);
  } else if (result && "view" in result && result.view === "error") {
    root.innerHTML = renderError(result.message, escapeHtml);
  } else {
    root.innerHTML = renderError("No action intent was provided to this confirmation view.", escapeHtml);
  }

  bindActionHandlers(root, escapeHtml);
  notifyActionHeight(root);
}

function isActionToolResult(value: ActionRenderResult): value is ActionToolResult {
  return Boolean(value && typeof value === "object" && "status" in value && value.status === "completed");
}

function renderConfirmation(intent: CriticalActionPublicIntent, escapeHtml: EscapeHtml): string {
  return `
    <div class="widget-stack action-shell">
      <header class="widget-hero action-hero">
        <div>
          <p class="widget-kicker">Human approval required</p>
          <h1>${escapeHtml(intent.actionLabel)}</h1>
          <p>${escapeHtml(intent.title)}</p>
        </div>
        <span class="action-chip">${escapeHtml(intent.portal)}</span>
      </header>

      <section class="widget-card widget-card-wide action-card">
        <div class="widget-card-header">
          <div>
            <p class="widget-kicker">Action intent</p>
            <h2>Nothing has been submitted yet</h2>
          </div>

        </div>

        <div class="action-facts">
          <div>
            <span>Target</span>
            <strong>${escapeHtml(intent.title)}</strong>
          </div>
          <div>
            <span>Prepared</span>
            <strong>${escapeHtml(formatTimestamp(intent.preparedAt))}</strong>
          </div>
          <div>
            <span>Expires</span>
            <strong>${escapeHtml(formatTimestamp(intent.expiresAt))}</strong>
          </div>
        </div>

        ${intent.targetUrl ? `<p class="action-url">${escapeHtml(intent.targetUrl)}</p>` : ""}

        <div class="action-section">
          <h3>What Proceed will do</h3>
          <ul>
            ${intent.sideEffects.map((effect) => `<li>${escapeHtml(effect)}</li>`).join("")}
          </ul>
        </div>

        ${
          intent.requiredInputs.length
            ? `
              <div class="action-section">
                <h3>Required inputs</h3>
                <ul>${intent.requiredInputs.map((input) => `<li>${escapeHtml(input)}</li>`).join("")}</ul>
              </div>
            `
            : ""
        }

        ${intent.requiresEnrolmentKey ? '<label class="action-section">Course enrolment key <input id="enrolment-key" type="password" autocomplete="off" maxlength="256" required></label>' : ""}
        <div class="action-controls">
          <button class="widget-button danger" data-action="proceed-critical-action" ${isSubmitting || !confirmationToken || Date.parse(intent.expiresAt) <= Date.now() ? "disabled" : ""}>
            ${isSubmitting ? "Submitting..." : "Proceed"}
          </button>
          <button class="widget-button ghost" data-action="cancel-critical-action" ${isSubmitting ? "disabled" : ""}>
            Cancel
          </button>
        </div>
      </section>
    </div>
  `;
}

function renderCompleted(result: ActionToolResult, escapeHtml: EscapeHtml): string {
  return `
    <div class="widget-stack action-shell">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">Action result</p>
          <h1>${escapeHtml(result.intent.actionLabel)}</h1>
          <p>${escapeHtml(result.result.message ?? `Finished with status ${result.result.status}.`)}</p>
        </div>
        <button class="widget-button ghost" data-action="close-action">Close</button>
      </header>
      <section class="widget-card widget-card-wide">
        <div class="action-facts">
          <div>
            <span>Status</span>
            <strong>${escapeHtml(result.result.status)}</strong>
          </div>
          <div>
            <span>Portal</span>
            <strong>${escapeHtml(result.intent.portal)}</strong>
          </div>
        </div>
        ${result.result.finalUrl ? `<p class="action-url">${escapeHtml(result.result.finalUrl)}</p>` : ""}
      </section>
    </div>
  `;
}

function renderCancelled(escapeHtml: EscapeHtml): string {
  return `
    <div class="widget-empty">
      <p class="widget-kicker">Cancelled</p>
      <h1>No action was submitted</h1>
      <p>${escapeHtml("The server discarded the prepared action. Upstream university state was not changed.")}</p>
    </div>
  `;
}

function renderError(message: string, escapeHtml: EscapeHtml): string {
  return `
    <div class="widget-empty">
      <p class="widget-kicker">Action unavailable</p>
      <h1>Confirmation failed</h1>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function bindActionHandlers(root: HTMLElement, escapeHtml: EscapeHtml) {
  root.onclick = (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const actionTarget = target.closest<HTMLElement>("[data-action]");
    if (!actionTarget?.dataset.action) {
      return;
    }
    event.preventDefault();
    void handleAction(actionTarget.dataset.action, root, escapeHtml);
  };
}

async function handleAction(action: string, root: HTMLElement, escapeHtml: EscapeHtml) {
  if (isSubmitting) return;
  if (action === "cancel-critical-action" && isCriticalActionView(currentResult)) {
    const intentId = currentResult.intent.id;
    const token = confirmationToken;
    isSubmitting = true;
    renderActionTemplate(root, currentResult, { confirmationToken }, escapeHtml);
    try {
      await callHostTool("cancel_critical_action", { intentId, confirmationToken: token });
      currentResult = null;
      confirmationToken = "";
      root.innerHTML = renderCancelled(escapeHtml);
      notifyActionHeight(root);
    } catch (error) {
      currentResult = { error: error instanceof Error ? error.message : "Cancellation could not be confirmed." };
      renderActionTemplate(root, currentResult, undefined, escapeHtml);
    } finally {
      isSubmitting = false;
    }
    return;
  }

  if (action === "close-action") {
    if (host()?.requestClose) {
      await host()?.requestClose?.();
    }
    return;
  }

  if (action !== "proceed-critical-action" || !isCriticalActionView(currentResult)) {
    return;
  }

  if (!confirmationToken) {
    root.innerHTML = renderError("The confirmation token is missing. Prepare the action again.", escapeHtml);
    return;
  }

  const enrolmentKey = root.querySelector<HTMLInputElement>("#enrolment-key")?.value;
  if (currentResult.intent.requiresEnrolmentKey && !enrolmentKey) {
    root.querySelector<HTMLInputElement>("#enrolment-key")?.reportValidity(); return;
  }
  isSubmitting = true;
  renderActionTemplate(root, currentResult, { confirmationToken }, escapeHtml);

  try {
    const result = await callHostTool<ActionToolResult>("confirm_critical_action", {
      intentId: currentResult.intent.id,
      confirmationToken,
      ...(enrolmentKey ? { enrolmentKey } : {}),
    });
    currentResult = result;
  } catch (error) {
    currentResult = { error: error instanceof Error ? error.message : "The action could not be submitted." };
  } finally {
    isSubmitting = false;
    confirmationToken = "";
    renderActionTemplate(root, currentResult, undefined, escapeHtml);
  }
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: "Europe/Berlin",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

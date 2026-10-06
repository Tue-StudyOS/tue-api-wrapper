import "./styles.css";
import { connectBridge, readToolMetadata } from "./widget-bridge.js";
import "./widget-layout-hardening.css";
import { connectHostAppearance } from "./host-appearance.js";
import { watchRenderedHeight } from "./widget-height.js";
import { isCriticalActionView, renderActionTemplate } from "./action-confirmation-render.js";
import { renderDocuments } from "./documents-render.js";
import { isMensaFoodPlanView, renderMensaFoodPlan } from "./mensa-render.js";
import { isModuleDetail, renderModuleDetailTemplate } from "./module-detail-render.js";
import { connectWidgetResultUpdates, readInitialWidgetResult } from "./widget-host-events.js";
import type { WidgetResult, WidgetViewResult } from "./widget-types.js";
import { state, isDetailTemplate, isActionTemplate } from "./widget-state.js";
import { escapeHtml } from "./widget-format.js";
import { getDashboard, isWidgetViewResult } from "./dashboard-data.js";
import { renderOverview } from "./overview-render.js";
import { renderSchedulePanel, renderTasksPanel, renderGradesPanel, renderSpacesPanel, renderCoursesPanel } from "./panel-render.js";
import { renderError, notifyRenderedHeight, renderDetailTemplate, renderAppShell } from "./shell-render.js";
import { createWidgetActions, invalidatePanelRequests, persistState } from "./widget-actions.js";
import "./widget-responsive.css";
const bindActions = createWidgetActions(render);







function renderPanel(): string {
  const dashboard = getDashboard();

  if (state.activePanel === "overview") {
    if (state.panelError) return renderError(state.panelError);
    if (!dashboard) {
      return renderError("The dashboard view is not available for this tool result.");
    }
    return renderOverview(dashboard);
  }

  if (state.loadingPanel === state.activePanel) {
    return `
      <article class="widget-card widget-card-wide">
        <p class="widget-kicker">Loading</p>
        <h2>Refreshing ${escapeHtml(state.activePanel)}</h2>
      </article>
    `;
  }

  if (state.panelError) {
    return `
      <article class="widget-card widget-card-wide">
        <p class="widget-kicker">Unavailable</p>
        <h2>${escapeHtml(state.activePanel)}</h2>
        <p role="alert">${escapeHtml(state.panelError)}</p>
        <button class="widget-button small" data-action="refresh-panel" data-panel="${state.activePanel}">Try again</button>
      </article>
    `;
  }

  switch (state.activePanel) {
    case "schedule":
      return renderSchedulePanel();
    case "tasks":
      return renderTasksPanel();
    case "grades":
      return renderGradesPanel();
    case "spaces":
      return renderSpacesPanel();
    case "courses":
      return renderCoursesPanel();
    default:
      return dashboard ? renderOverview(dashboard) : renderError("No dashboard data available.");
  }
}

function render(result: WidgetResult) {
  const root = document.getElementById("root");
  if (!root) {
    throw new Error("Missing root element");
  }

  state.result = result;

  if (isDetailTemplate) {
    root.innerHTML = renderDetailTemplate();
    bindActions(root);
    notifyRenderedHeight(root);
    return;
  }

  if (isActionTemplate) {
    renderActionTemplate(root, result as Parameters<typeof renderActionTemplate>[1], readToolMetadata(), escapeHtml);
    return;
  }

  if (!result) {
    root.innerHTML = `
      <div class="widget-empty">
        <p class="widget-kicker">Study Hub</p>
        <h1>Waiting for data</h1>
        <p>Call the dashboard tool to populate this view.</p>
      </div>
    `;
    notifyRenderedHeight(root);
    return;
  }

  if (isModuleDetail(result)) {
    root.innerHTML = renderModuleDetailTemplate(result, escapeHtml);
  } else if (isMensaFoodPlanView(result)) {
    root.innerHTML = renderMensaFoodPlan(result);
  } else if (!isWidgetViewResult(result)) {
    root.innerHTML = renderError("The widget received an unsupported Alma detail payload.");
  } else {
    root.innerHTML =
      result.view === "documents"
        ? renderDocuments(result.documents)
        : result.view === "error"
          ? renderError(result.message)
          : isCriticalActionView(result)
            ? renderError("Open this action from its confirmation UI.")
          : result.view === "course-detail"
            ? renderModuleDetailTemplate(result.detail, escapeHtml)
            : renderAppShell(renderPanel());
  }

  bindActions(root);
  notifyRenderedHeight(root);
}

connectHostAppearance((expanded) => {
  if (expanded !== state.expanded) {
    state.expanded = expanded;
    persistState();
    render(state.result);
  }
});

connectWidgetResultUpdates((result) => {
  if (isWidgetViewResult(result as WidgetResult) && (result as WidgetViewResult).view === "dashboard") {
    state.panelCache = {};
    state.loadingPanel = null;
    state.panelError = null;
    invalidatePanelRequests();
  }
  render(result as WidgetResult);
});
if (!window.openai?.callTool && window.parent !== window) {
  void connectBridge().catch((error: unknown) => render({ view: "error", message: error instanceof Error ? error.message : "Host connection failed." }));
}
render(readInitialWidgetResult() as WidgetResult);
watchRenderedHeight(document.getElementById("root")!);

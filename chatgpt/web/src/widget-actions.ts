import type { AlmaCourseSearchResponse, IliasTaskItem, IliasMembershipItem, AlmaExamRecord } from "../../src/types.js";
import type { WidgetResult, PanelName, PanelCache, DetailPayload, StudySummaryPanel } from "./widget-types.js";
import { state, detailWidgetUri, sanitizePanel } from "./widget-state.js";
import { getDashboard } from "./dashboard-data.js";
import { decodeData } from "./widget-format.js";
import { bindMensaFoodPlanActions } from "./mensa-render.js";
import { callHostTool, sendFollowUp, requestDisplayMode } from "./widget-bridge.js";

let panelRequestId = 0;
export function invalidatePanelRequests() { ++panelRequestId; }

export function createWidgetActions(render: (result: WidgetResult) => void) {
async function callTool<T>(name: string, args: Record<string, unknown> = {}): Promise<T> {
  return callHostTool<T>(name, args);
}

async function loadPanel(panel: Exclude<PanelName, "overview">) {
  const requestId = ++panelRequestId;
  state.loadingPanel = panel;
  state.panelError = null;
  render(state.result);

  try {
    if (panel === "schedule") {
      const data = await callTool<NonNullable<PanelCache["schedule"]>>("get_upcoming_schedule", { limit: 10 });
      if (requestId === panelRequestId) {
        const dashboard = getDashboard();
        state.panelCache.schedule = {
          ...data,
          currentSemesterCredits: data.currentSemesterCredits ?? dashboard?.study.currentSemesterCredits ?? null,
          currentSemesterCreditCourses: data.currentSemesterCreditCourses ?? dashboard?.study.currentSemesterCreditCourses ?? 0
        };
      }
    } else if (panel === "tasks") {
      const data = await callTool<{ tasks: IliasTaskItem[] }>("get_current_tasks", { limit: 12 });
      if (requestId === panelRequestId) {
        state.panelCache.tasks = data;
      }
    } else if (panel === "grades") {
      const data = await callTool<{ study: StudySummaryPanel; exams: AlmaExamRecord[] }>("get_current_grades", { limit: 16 });
      if (requestId === panelRequestId) {
        state.panelCache.grades = data;
      }
    } else if (panel === "spaces") {
      const data = await callTool<{ memberships: IliasMembershipItem[] }>("get_learning_spaces", { limit: 12 });
      if (requestId === panelRequestId) {
        state.panelCache.spaces = data;
      }
    } else if (panel === "courses") {
      const query = state.courseQuery.trim();
      if (!query) {
        state.panelCache.courses = undefined;
      } else {
        const data = await callTool<AlmaCourseSearchResponse>("search_courses", { query, maxResults: 8 });
        if (requestId === panelRequestId) {
          state.panelCache.courses = {
            ...data,
            query
          };
        }
      }
    }
  } catch (error) {
    if (requestId === panelRequestId) state.panelError = error instanceof Error ? error.message : "Panel refresh failed.";
  } finally {
    if (requestId === panelRequestId) {
      state.loadingPanel = null;
      render(state.result);
    }
  }
}

function setPanel(panel: PanelName) {
  invalidatePanelRequests();
  state.loadingPanel = null;
  state.activePanel = panel;
  state.panelError = null;
  persistState();
  render(state.result);

  if (panel !== "overview") {
    void loadPanel(panel);
  }
}

async function openDetail(detail: DetailPayload) {
  state.detailModal = detail;
  state.inlineDetailOpen = false;
  persistState();

  if (window.openai?.requestModal) {
    await window.openai.requestModal({ template: detailWidgetUri });
    return;
  }

  state.inlineDetailOpen = true;
  render(state.result);
}

async function openExternal(href: string) {
  if (window.openai?.openExternal) {
    await window.openai.openExternal({ href });
    return;
  }
  window.open(href, "_blank", "noopener,noreferrer");
}

async function setExpanded(expanded: boolean) {
  const mode = await requestDisplayMode(expanded ? "fullscreen" : "inline");
  if (expanded && mode !== "fullscreen") throw new Error("The host could not open fullscreen. Ask for a specific schedule, task, or grade view instead.");
  state.expanded = mode === "fullscreen";
  persistState();
  render(state.result);

}

async function handleAction(element: HTMLElement) {
  const action = element.dataset.action;
  if (!action) {
    return;
  }

  if (action === "set-panel") {
    setPanel(sanitizePanel(element.dataset.panel));
    return;
  }

  if (action === "refresh-panel") {
    const panel = sanitizePanel(element.dataset.panel);
    if (panel !== "overview") {
      void loadPanel(panel);
    }
    return;
  }

  if (action === "open-detail") {
    const detail = decodeData<DetailPayload>(element.dataset.detail);
    if (detail) {
      await openDetail(detail);
    }
    return;
  }

  if (action === "dismiss-inline-detail") {
    state.inlineDetailOpen = false;
    render(state.result);
    return;
  }

  if (action === "close-modal") {
    state.detailModal = null;
    persistState();
    if (window.openai?.requestClose) {
      await window.openai.requestClose();
    } else {
      render(state.result);
    }
    return;
  }

  if (action === "open-external" && element.dataset.href) {
    await openExternal(element.dataset.href);
    return;
  }

  if (action === "toggle-expand") {
    await setExpanded(!state.expanded);
  }
}

function bindActions(root: HTMLElement) {
  root.onclick = (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const actionTarget = target.closest<HTMLElement>("[data-action]");
    if (actionTarget) {
      event.preventDefault();
      void handleAction(actionTarget).catch((error: unknown) => {
        state.panelError = error instanceof Error ? error.message : "This action could not be completed.";
        render(state.result);
      });
      return;
    }

    const followUpTarget = target.closest<HTMLElement>("[data-follow-up]");
    if (followUpTarget?.dataset.followUp) {
      event.preventDefault();
      postFollowUp(followUpTarget.dataset.followUp);
    }
  };

  const searchForm = root.querySelector<HTMLFormElement>("form[data-action='search-courses']");
  if (searchForm) {
    searchForm.onsubmit = (event) => {
      event.preventDefault();
      const input = searchForm.elements.namedItem("courseQuery");
      if (!(input instanceof HTMLInputElement)) {
        return;
      }
      state.courseQuery = input.value;
      persistState();
      void loadPanel("courses");
    };
  }

  bindMensaFoodPlanActions(root, callTool, (nextResult) => render(nextResult as WidgetResult));
}

function postFollowUp(prompt: string) {
  void sendFollowUp(prompt).catch((error: unknown) => {
    state.panelError = error instanceof Error ? error.message : "The message could not be sent.";
    render(state.result);
  });
}
return bindActions;
}

export function persistState() {
  window.openai?.setWidgetState?.({ activePanel: state.activePanel, courseQuery: state.courseQuery, expanded: state.expanded, privateContent: { detailModal: state.detailModal } });
}

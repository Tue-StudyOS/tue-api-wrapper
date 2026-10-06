import type { DashboardPayload, ModuleDetail } from "../../src/types.js";
import type { WidgetResult, WidgetViewResult, PanelCache } from "./widget-types.js";
import { state } from "./widget-state.js";
import { isModuleDetail } from "./module-detail-render.js";

export function getRenderedModuleDetail(): ModuleDetail | null {
  const result = state.result;
  if (isModuleDetail(result)) {
    return result;
  }
  if (isWidgetViewResult(result) && result.view === "course-detail") {
    return result.detail;
  }
  return null;
}

export function isWidgetViewResult(value: WidgetResult): value is WidgetViewResult {
  return Boolean(value && typeof value === "object" && "view" in value);
}

export function getDashboard(): DashboardPayload | null {
  const result = state.result;
  return isWidgetViewResult(result) && result.view === "dashboard" ? result.dashboard : null;
}

export function getGradesPanelData(): NonNullable<PanelCache["grades"]> {
  if (state.panelCache.grades) {
    return state.panelCache.grades;
  }

  const dashboard = getDashboard();
  return {
    study: dashboard?.study ?? {
      selectedTerm: null,
      message: null,
      passedExamCount: 0,
      trackedCredits: 0,
      currentSemesterCredits: null,
      currentSemesterCreditCourses: 0,
      currentSemesterCreditUnresolved: [],
      currentSemesterCreditError: null
    },
    exams: dashboard?.exams ?? []
  };
}

export function getSchedulePanelData(): NonNullable<PanelCache["schedule"]> {
  if (state.panelCache.schedule) {
    return state.panelCache.schedule;
  }

  const dashboard = getDashboard();
  return {
    termLabel: dashboard?.termLabel ?? "Current term",
    exportUrl: dashboard?.agenda.exportUrl ?? "",
    items: dashboard?.agenda.items ?? [],
    currentSemesterCredits: dashboard?.study.currentSemesterCredits ?? null,
    currentSemesterCreditCourses: dashboard?.study.currentSemesterCreditCourses ?? 0
  };
}

export function getTasksPanelData(): NonNullable<PanelCache["tasks"]> {
  if (state.panelCache.tasks) {
    return state.panelCache.tasks;
  }

  const dashboard = getDashboard();
  return {
    tasks: dashboard?.ilias.tasks ?? []
  };
}

export function getSpacesPanelData(): NonNullable<PanelCache["spaces"]> {
  if (state.panelCache.spaces) {
    return state.panelCache.spaces;
  }

  const dashboard = getDashboard();
  return {
    memberships: dashboard?.ilias.memberships ?? []
  };
}

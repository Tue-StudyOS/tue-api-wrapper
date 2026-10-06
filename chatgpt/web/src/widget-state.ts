import type { WidgetResult, WidgetState, PanelName } from "./widget-types.js";
import { readInitialWidgetResult } from "./widget-host-events.js";

export const detailWidgetUri = "ui://study-hub/detail-v9.html";
export const isDetailTemplate = document.body.dataset.template === "detail";
export const isActionTemplate = document.body.dataset.template === "action";

export const state: WidgetState = {
  result: readInitialWidgetResult() as WidgetResult,
  activePanel: sanitizePanel(window.openai?.widgetState?.activePanel),
  courseQuery: window.openai?.widgetState?.courseQuery ?? "",
  detailModal: window.openai?.widgetState?.privateContent?.detailModal ?? null,
  panelCache: {},
  loadingPanel: null,
  panelError: null,
  inlineDetailOpen: false,
  expanded: window.openai?.displayMode === "fullscreen"
};

export function sanitizePanel(value: string | undefined): PanelName {
  switch (value) {
    case "schedule":
    case "tasks":
    case "grades":
    case "spaces":
    case "courses":
      return value;
    default:
      return "overview";
  }
}

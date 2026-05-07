import "./styles.css";
import "./widget-layout-hardening.css";
import { isCriticalActionView, renderActionTemplate } from "./action-confirmation-render.js";
import { renderDocuments } from "./documents-render.js";
import { bindMensaFoodPlanActions, isMensaFoodPlanView, renderMensaFoodPlan } from "./mensa-render.js";
import { isModuleDetail, renderModuleDetailTemplate } from "./module-detail-render.js";
import { connectWidgetResultUpdates, readInitialWidgetResult } from "./widget-host-events.js";
import type {
  AgendaItem,
  AlmaCourseSearchResponse,
  AlmaExamRecord,
  DashboardPayload,
  DocumentsSummaryPayload,
  IliasMembershipItem,
  IliasTaskItem,
  ModuleDetail,
  CampusFoodPlanView,
  CriticalActionView
} from "../../src/types.js";

type WidgetResult =
  | {
      view: "dashboard";
      dashboard: DashboardPayload;
    }
  | {
      view: "documents";
      documents: DocumentsSummaryPayload;
    }
  | {
      view: "course-detail";
      detail: ModuleDetail;
    }
  | CampusFoodPlanView
  | {
      view: "error";
      message: string;
    }
  | CriticalActionView
  | ModuleDetail
  | null;
type WidgetViewResult = Exclude<WidgetResult, ModuleDetail | null>;
type DisplayMode = "inline" | "pip" | "fullscreen";

type PanelName = "overview" | "schedule" | "tasks" | "grades" | "spaces" | "courses";

interface StudySummaryPanel {
  selectedTerm: string | null;
  message: string | null;
  passedExamCount: number;
  trackedCredits: number;
  currentSemesterCredits?: number | null;
  currentSemesterCreditCourses?: number;
  currentSemesterCreditUnresolved?: string[];
  currentSemesterCreditError?: string | null;
}

interface DetailPayload {
  title: string;
  subtitle?: string;
  lines: string[];
  href?: string;
  hrefLabel?: string;
}

interface PersistedWidgetState {
  activePanel?: PanelName;
  courseQuery?: string;
  detailModal?: DetailPayload | null;
  expanded?: boolean;
}

interface PanelCache {
  schedule?: {
    termLabel: string;
    exportUrl: string;
    items: AgendaItem[];
    currentSemesterCredits?: number | null;
    currentSemesterCreditCourses?: number;
  };
  tasks?: {
    tasks: IliasTaskItem[];
  };
  grades?: {
    study: StudySummaryPanel;
    exams: AlmaExamRecord[];
  };
  spaces?: {
    memberships: IliasMembershipItem[];
  };
  courses?: AlmaCourseSearchResponse & { query: string };
}

interface WidgetState {
  result: WidgetResult;
  activePanel: PanelName;
  courseQuery: string;
  detailModal: DetailPayload | null;
  panelCache: PanelCache;
  loadingPanel: PanelName | null;
  panelError: string | null;
  inlineDetailOpen: boolean;
  expanded: boolean;
}

interface ToolCallResult<T = unknown> {
  structuredContent?: T;
  content?: Array<{ type: string; text?: string }>;
  _meta?: Record<string, unknown>;
}

declare global {
  interface Window {
    openai?: {
      toolInput?: Record<string, unknown>;
      toolOutput?: WidgetResult;
      toolResponseMetadata?: Record<string, unknown>;
      widgetState?: PersistedWidgetState;
      setWidgetState?: (state: PersistedWidgetState) => void;
      callTool?: <T = unknown>(name: string, args?: Record<string, unknown>) => Promise<ToolCallResult<T>>;
      requestModal?: (args?: {
        template?: string;
        params?: Record<string, unknown>;
      }) => Promise<void>;
      requestClose?: () => Promise<void>;
      requestDisplayMode?: (args: { mode: DisplayMode }) => Promise<void>;
      displayMode?: DisplayMode;
      maxHeight?: number;
      openExternal?: (args: { href: string; redirectUrl?: string | false }) => Promise<void>;
      sendFollowUpMessage?: (args: {
        prompt: string;
        scrollToBottom?: boolean;
      }) => Promise<void>;
      notifyIntrinsicHeight?: (height?: number) => void;
    };
  }
}

const detailWidgetUri = "ui://study-hub/detail-v7.html";
const isDetailTemplate = document.body.dataset.template === "detail";
const isActionTemplate = document.body.dataset.template === "action";

const state: WidgetState = {
  result: readInitialWidgetResult() as WidgetResult,
  activePanel: sanitizePanel(window.openai?.widgetState?.activePanel),
  courseQuery: window.openai?.widgetState?.courseQuery ?? "",
  detailModal: window.openai?.widgetState?.detailModal ?? null,
  panelCache: {},
  loadingPanel: null,
  panelError: null,
  inlineDetailOpen: false,
  expanded: window.openai?.displayMode === "fullscreen" || window.openai?.widgetState?.expanded === true
};

function sanitizePanel(value: string | undefined): PanelName {
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

function escapeHtml(value: string | null | undefined): string {
  return (value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function encodeData(value: unknown): string {
  return encodeURIComponent(JSON.stringify(value));
}

function decodeData<T>(value: string | undefined): T | null {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(decodeURIComponent(value)) as T;
  } catch {
    return null;
  }
}

function getRenderedModuleDetail(): ModuleDetail | null {
  const result = state.result;
  if (isModuleDetail(result)) {
    return result;
  }
  if (isWidgetViewResult(result) && result.view === "course-detail") {
    return result.detail;
  }
  return null;
}

function isWidgetViewResult(value: WidgetResult): value is WidgetViewResult {
  return Boolean(value && typeof value === "object" && "view" in value);
}

function postFollowUp(prompt: string) {
  if (window.openai?.sendFollowUpMessage) {
    void window.openai.sendFollowUpMessage({ prompt });
    return;
  }

  window.parent.postMessage(
    {
      jsonrpc: "2.0",
      id: `follow-up-${Date.now()}`,
      method: "ui/message",
      params: { prompt }
    },
    "*"
  );
}

function persistState() {
  const snapshot: PersistedWidgetState = {
    activePanel: state.activePanel,
    courseQuery: state.courseQuery,
    detailModal: state.detailModal,
    expanded: state.expanded
  };
  window.openai?.setWidgetState?.(snapshot);
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Date pending";
  }
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatRelativeStart(value: string): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const diffMinutes = Math.round((date.getTime() - Date.now()) / (1000 * 60));

  if (Math.abs(diffMinutes) < 60) {
    return relative.format(diffMinutes, "minute");
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 48) {
    return relative.format(diffHours, "hour");
  }

  return relative.format(Math.round(diffHours / 24), "day");
}

function formatCredits(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "Unavailable";
  }
  return `${Number.isInteger(value) ? value : value.toFixed(1).replace(/\.0$/, "")} CP`;
}

function renderFallbackRow(message: string): string {
  return `
    <div class="widget-row compact">
      <strong>${escapeHtml(message)}</strong>
    </div>
  `;
}

function renderDetailButton(detail: DetailPayload): string {
  return `
    <button class="widget-button ghost small" data-action="open-detail" data-detail="${encodeData(detail)}">
      Details
    </button>
  `;
}

function agendaLocation(item: AgendaItem): string | null {
  return item.room_details?.display_text ?? item.location ?? null;
}

function buildAgendaDetail(item: AgendaItem): DetailPayload {
  const room = item.room_details;
  const lines = [
    `Start: ${formatDate(item.start)}`,
    item.end ? `End: ${formatDate(item.end)}` : "End: not provided",
    item.description ? `Notes: ${item.description}` : "Notes: no extra description"
  ];
  if (room?.floor_default) {
    lines.push(`Floor: ${room.floor_default}`);
  }
  if (room?.building_default) {
    lines.push(`Building: ${room.building_default}`);
  }
  if (room?.campus_default) {
    lines.push(`Campus: ${room.campus_default}`);
  }
  return {
    title: item.summary,
    subtitle: agendaLocation(item) ?? "Alma schedule item",
    lines,
    href: room?.detail_url ?? undefined,
    hrefLabel: room?.detail_url ? "Open Alma room details" : undefined
  };
}

function renderAgendaRow(item: AgendaItem, accent = "teal"): string {
  const relativeStart = formatRelativeStart(item.start);
  const location = agendaLocation(item);

  return `
    <div class="widget-row widget-agenda-row" data-accent="${accent}">
      <div class="widget-agenda-time">
        <strong>${escapeHtml(formatDate(item.start))}</strong>
        ${relativeStart ? `<span>${escapeHtml(relativeStart)}</span>` : ""}
      </div>
      <div class="widget-agenda-content">
        <strong>${escapeHtml(item.summary)}</strong>
        <p>${escapeHtml(location ?? "Location pending")}</p>
      </div>
      <div class="widget-row-actions">
        ${renderDetailButton(buildAgendaDetail(item))}
      </div>
    </div>
  `;
}

function buildTaskDetail(item: IliasTaskItem): DetailPayload {
  return {
    title: item.title,
    subtitle: item.item_type ?? "ILIAS task",
    lines: [
      `Start: ${item.start ?? "-"}`,
      `End: ${item.end ?? "-"}`,
      "This item came from the authenticated ILIAS derived tasks overview."
    ],
    href: item.url,
    hrefLabel: "Open source"
  };
}

function buildMembershipDetail(item: IliasMembershipItem): DetailPayload {
  return {
    title: item.title,
    subtitle: item.kind ?? "Learning space",
    lines: [
      item.description ?? "No description exposed by ILIAS.",
      ...item.properties
    ].filter(Boolean),
    href: item.url,
    hrefLabel: "Open source"
  };
}

function buildExamDetail(item: AlmaExamRecord): DetailPayload {
  return {
    title: item.title,
    subtitle: item.number ?? item.kind ?? "Alma exam record",
    lines: [
      `Grade: ${item.grade ?? "-"}`,
      `Status: ${item.status ?? "-"}`,
      `Credits: ${item.cp ?? "-"}`,
      `Attempt: ${item.attempt ?? "-"}`,
      `Release date: ${item.release_date ?? "-"}`
    ]
  };
}

function buildCourseDetail(result: NonNullable<PanelCache["courses"]>["results"][number]): DetailPayload {
  return {
    title: result.title,
    subtitle: result.number ?? result.element_type ?? "Alma module search result",
    lines: [
      `Element type: ${result.element_type ?? "-"}`,
      result.detail_url ? "A public Alma detail page is available for this result." : "No public detail URL exposed."
    ],
    href: result.detail_url ?? undefined,
    hrefLabel: result.detail_url ? "Open source" : undefined
  };
}

function buildTalkDetail(item: DashboardPayload["talks"]["items"][number]): DetailPayload {
  return {
    title: item.title,
    subtitle: item.speaker_name ?? item.location ?? "Talk",
    lines: [
      `Time: ${formatDate(item.timestamp)}`,
      `Location: ${item.location ?? "-"}`,
      `Speaker: ${item.speaker_name ?? "-"}`,
      item.description ? `Abstract: ${item.description}` : "Abstract: not provided"
    ],
    href: item.source_url,
    hrefLabel: "Open original talk"
  };
}

function getDashboard(): DashboardPayload | null {
  const result = state.result;
  return isWidgetViewResult(result) && result.view === "dashboard" ? result.dashboard : null;
}

function getGradesPanelData(): NonNullable<PanelCache["grades"]> {
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

function getSchedulePanelData(): NonNullable<PanelCache["schedule"]> {
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

function getTasksPanelData(): NonNullable<PanelCache["tasks"]> {
  if (state.panelCache.tasks) {
    return state.panelCache.tasks;
  }

  const dashboard = getDashboard();
  return {
    tasks: dashboard?.ilias.tasks ?? []
  };
}

function getSpacesPanelData(): NonNullable<PanelCache["spaces"]> {
  if (state.panelCache.spaces) {
    return state.panelCache.spaces;
  }

  const dashboard = getDashboard();
  return {
    memberships: dashboard?.ilias.memberships ?? []
  };
}

function renderOverview(dashboard: DashboardPayload): string {
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
            <p>${escapeHtml(item.trigger_name)}</p>
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

function renderSchedulePanel(): string {
  const data = getSchedulePanelData();
  const nextItem = data.items[0];
  const rows = data.items
    .slice(0, 10)
    .map((item, index) => renderAgendaRow(item, index === 0 ? "teal" : "rose"))
    .join("") || renderFallbackRow("No upcoming Alma events found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Schedule</p>
          <h2>${escapeHtml(data.termLabel)}</h2>
        </div>
        <div class="widget-card-actions">
          ${data.exportUrl ? `<a class="widget-button ghost small" href="${escapeHtml(data.exportUrl)}" target="_blank" rel="noreferrer">Export</a>` : ""}
          <button class="widget-button small" data-action="refresh-panel" data-panel="schedule">Refresh</button>
        </div>
      </div>
      <div class="widget-summary">
        <div>
          <span>Next up</span>
          <strong>${escapeHtml(nextItem ? formatRelativeStart(nextItem.start) ?? formatDate(nextItem.start) : "Nothing queued")}</strong>
        </div>
        <div>
          <span>Saved semester</span>
          <strong>${formatCredits(data.currentSemesterCredits)}</strong>
        </div>
        <div>
          <span>Visible items</span>
          <strong>${data.items.length}</strong>
        </div>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

function renderTasksPanel(): string {
  const data = getTasksPanelData();
  const rows = data.tasks
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

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Tasks</p>
          <h2>ILIAS due items</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="tasks">Refresh</button>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

function renderGradesPanel(): string {
  const data = getGradesPanelData();
  const rows = data.exams
    .slice(0, 16)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml([item.number, item.cp ? `${item.cp} CP` : null, item.attempt ? `Attempt ${item.attempt}` : null].filter(Boolean).join(" · ") || item.status || "No structured metadata")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.grade ?? item.status ?? "-")}</span>
            ${renderDetailButton(buildExamDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No Alma exam rows found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Grades</p>
          <h2>Study progress</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="grades">Refresh</button>
      </div>
      <div class="widget-summary">
        <div>
          <span>Saved semester</span>
          <strong>${formatCredits(data.study.currentSemesterCredits)}</strong>
        </div>
        <div>
          <span>Tracked credits</span>
          <strong>${data.study.trackedCredits}</strong>
        </div>
        <div>
          <span>Passed exams</span>
          <strong>${data.study.passedExamCount}</strong>
        </div>
        <div>
          <span>Term</span>
          <strong>${escapeHtml(data.study.selectedTerm ?? "Unknown")}</strong>
        </div>
      </div>
      <div class="widget-list">${rows}</div>
      ${data.study.message ? `<p class="widget-panel-note">${escapeHtml(data.study.message)}</p>` : ""}
    </article>
  `;
}

function renderSpacesPanel(): string {
  const data = getSpacesPanelData();
  const rows = data.memberships
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

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Spaces</p>
          <h2>Current learning spaces</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="spaces">Refresh</button>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

function renderCoursesPanel(): string {
  const data = state.panelCache.courses;
  const rows = data?.results
    .slice(0, 8)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml([item.number, item.element_type].filter(Boolean).join(" · ") || "Alma result")}</p>
          </div>
          <div class="widget-row-actions">
            ${renderDetailButton(buildCourseDetail(item))}
          </div>
        </div>
      `
    )
    .join("");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Courses</p>
          <h2>Search next semester options</h2>
        </div>
        <button class="widget-button ghost small" data-follow-up="Suggest courses for next semester based on my study progress and current degree.">
          Ask model
        </button>
      </div>
      <form class="widget-search" data-action="search-courses">
        <input
          class="widget-input"
          type="text"
          name="courseQuery"
          placeholder="Search modules or courses"
          value="${escapeHtml(state.courseQuery)}"
        />
        <button class="widget-button small" type="submit">Search</button>
      </form>
      ${
        data
          ? `
            <p class="widget-panel-note">
              ${escapeHtml(`Showing ${data.returnedResults} result${data.returnedResults === 1 ? "" : "s"}${data.totalResults !== null ? ` of ${data.totalResults}` : ""} for "${data.query}".`)}
            </p>
          `
          : `
            <p class="widget-panel-note">
              Search the Alma catalog directly from the widget. This uses the read-only course discovery tools without remounting the app.
            </p>
          `
      }
      <div class="widget-list">
        ${rows || renderFallbackRow(data ? "No Alma course results matched this query." : "No course search has been run yet.")}
      </div>
    </article>
  `;
}

function renderPanel(): string {
  const dashboard = getDashboard();

  if (state.activePanel === "overview") {
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
        <p>${escapeHtml(state.panelError)}</p>
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

function renderError(message: string): string {
  return `
    <div class="widget-empty">
      <p class="widget-kicker">Live data required</p>
      <h1>Backend unavailable</h1>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function notifyRenderedHeight(root: HTMLElement) {
  const shell = root.querySelector<HTMLElement>(".widget-shell, .widget-modal-stack, .action-shell, .widget-empty");
  if (!shell) {
    window.openai?.notifyIntrinsicHeight?.();
    return;
  }
  window.openai?.notifyIntrinsicHeight?.(Math.ceil(shell.getBoundingClientRect().height));
}

function renderDetailTemplate(): string {
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

function renderAppShell(content: string): string {
  const dashboard = getDashboard();
  const panelTabs: Array<{ key: PanelName; label: string }> = [
    { key: "overview", label: "Overview" },
    { key: "schedule", label: "Schedule" },
    { key: "tasks", label: "Tasks" },
    { key: "grades", label: "Grades" },
    { key: "spaces", label: "Spaces" },
    { key: "courses", label: "Courses" }
  ];

  return `
    <div class="widget-stack widget-shell${state.expanded ? " is-expanded" : ""}">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">${escapeHtml(dashboard?.termLabel ?? "Study Hub")}</p>
          <h1>${escapeHtml(dashboard?.hero.title ?? "Study Hub")}</h1>
          <p>${escapeHtml(dashboard?.hero.subtitle ?? "Use the panels below to explore live study data without remounting the widget.")}</p>
        </div>
        <div class="widget-card-actions">
          <button class="widget-button ghost small" data-action="toggle-expand" aria-pressed="${state.expanded}">
            ${state.expanded ? "Collapse" : "Expand"}
          </button>
          <button class="widget-button ghost small" data-follow-up="Summarize the most urgent things in my study dashboard.">Summarize</button>
        </div>
      </header>

      <nav class="widget-tabs" aria-label="Study dashboard panels">
        ${panelTabs
          .map(
            (tab) => `
              <button
                class="widget-tab${state.activePanel === tab.key ? " is-active" : ""}"
                data-action="set-panel"
                data-panel="${tab.key}"
              >
                ${escapeHtml(tab.label)}
              </button>
            `
          )
          .join("")}
      </nav>

      <main class="widget-scroll" tabindex="0">
        ${content}

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

      ${
        dashboard?.generatedAt
          ? `
            <footer class="widget-footer-meta">
              Last updated ${escapeHtml(
                new Intl.DateTimeFormat("de-DE", {
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
    renderActionTemplate(root, isCriticalActionView(result) ? result : null, window.openai?.toolResponseMetadata, escapeHtml);
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

async function callTool<T>(name: string, args: Record<string, unknown> = {}): Promise<T | null> {
  if (!window.openai?.callTool) {
    throw new Error("Direct tool calls are only available inside the ChatGPT host.");
  }
  const response = await window.openai.callTool<T>(name, args);
  return response.structuredContent ?? null;
}

async function loadPanel(panel: Exclude<PanelName, "overview">) {
  state.loadingPanel = panel;
  state.panelError = null;
  render(state.result);

  try {
    if (panel === "schedule") {
      const data = await callTool<NonNullable<PanelCache["schedule"]>>("get_upcoming_schedule", { limit: 10 });
      if (data) {
        const dashboard = getDashboard();
        state.panelCache.schedule = {
          ...data,
          currentSemesterCredits: data.currentSemesterCredits ?? dashboard?.study.currentSemesterCredits ?? null,
          currentSemesterCreditCourses: data.currentSemesterCreditCourses ?? dashboard?.study.currentSemesterCreditCourses ?? 0
        };
      }
    } else if (panel === "tasks") {
      const data = await callTool<{ tasks: IliasTaskItem[] }>("get_current_tasks", { limit: 12 });
      if (data) {
        state.panelCache.tasks = data;
      }
    } else if (panel === "grades") {
      const data = await callTool<{ study: StudySummaryPanel; exams: AlmaExamRecord[] }>("get_current_grades", { limit: 16 });
      if (data) {
        state.panelCache.grades = data;
      }
    } else if (panel === "spaces") {
      const data = await callTool<{ memberships: IliasMembershipItem[] }>("get_learning_spaces", { limit: 12 });
      if (data) {
        state.panelCache.spaces = data;
      }
    } else if (panel === "courses") {
      const query = state.courseQuery.trim();
      if (!query) {
        state.panelCache.courses = undefined;
      } else {
        const data = await callTool<AlmaCourseSearchResponse>("search_courses", { query, maxResults: 8 });
        if (data) {
          state.panelCache.courses = {
            ...data,
            query
          };
        }
      }
    }
  } catch (error) {
    state.panelError = error instanceof Error ? error.message : "Panel refresh failed.";
  } finally {
    state.loadingPanel = null;
    render(state.result);
  }
}

function setPanel(panel: PanelName) {
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
  state.expanded = expanded;
  persistState();
  render(state.result);

  if (window.openai?.requestDisplayMode) {
    await window.openai.requestDisplayMode({ mode: expanded ? "fullscreen" : "inline" }).catch(() => undefined);
  }
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
      void handleAction(actionTarget);
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

window.addEventListener("openai:set_globals", (event) => {
  const customEvent = event as CustomEvent<{ globals?: { displayMode?: DisplayMode } }>;
  const displayMode = customEvent.detail?.globals?.displayMode;
  if (!displayMode) {
    return;
  }

  const expanded = displayMode === "fullscreen";
  if (expanded !== state.expanded) {
    state.expanded = expanded;
    persistState();
    render(state.result);
  }
});

connectWidgetResultUpdates((result) => render(result as WidgetResult));
render(readInitialWidgetResult() as WidgetResult);

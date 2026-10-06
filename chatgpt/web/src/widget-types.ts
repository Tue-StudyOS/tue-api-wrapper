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

export type WidgetResult =
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
export type WidgetViewResult = Exclude<WidgetResult, ModuleDetail | null>;
export type DisplayMode = "inline" | "pip" | "fullscreen";

export type PanelName = "overview" | "schedule" | "tasks" | "grades" | "spaces" | "courses";

export interface StudySummaryPanel {
  selectedTerm: string | null;
  message: string | null;
  passedExamCount: number;
  trackedCredits: number;
  currentSemesterCredits?: number | null;
  currentSemesterCreditCourses?: number;
  currentSemesterCreditUnresolved?: string[];
  currentSemesterCreditError?: string | null;
}

export interface DetailPayload {
  title: string;
  subtitle?: string;
  lines: string[];
  href?: string;
  hrefLabel?: string;
}

export interface PersistedWidgetState {
  activePanel?: PanelName;
  courseQuery?: string;
  privateContent?: { detailModal?: DetailPayload | null };
  expanded?: boolean;
}

export interface PanelCache {
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

export interface WidgetState {
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
  isError?: boolean;
}

declare global {
  interface Window {
    openai?: {
      theme?: "light" | "dark";
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
      requestDisplayMode?: (args: { mode: DisplayMode }) => Promise<{ mode: DisplayMode } | void>;
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

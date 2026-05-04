import type { DesktopRuntimeState } from "../../../shared/desktop-types";
import type { CampusSnapshot } from "../../lib/campus-types";
import type { CourseDiscoverySearchResponse, CourseDiscoveryStatus } from "../../lib/course-discovery-types";
import type { AlmaTimetableCourseAssignment, DashboardAgendaItem, DashboardData } from "../../lib/dashboard-types";
import type { MailboxSummary, MailInboxSummary } from "../../lib/mail-types";

export type DashboardPageId =
  | "today"
  | "calendar"
  | "learning"
  | "study"
  | "mail"
  | "campus"
  | "discovery"
  | "career"
  | "assistant"
  | "tools";

export interface DashboardPageProps {
  state: DesktopRuntimeState;
  data: DashboardData | null;
}

export interface CourseDetailTarget {
  title: string;
  url?: string | null;
  term?: string | null;
  sourceLabel?: string | null;
  event?: DashboardAgendaItem | null;
  assignment?: AlmaTimetableCourseAssignment | null;
}

export interface CourseNavigationProps {
  onOpenCourseDetail: (target: CourseDetailTarget) => void;
}

export interface CampusPageProps extends DashboardPageProps {
  campus: CampusSnapshot | null;
  campusLoading: boolean;
  campusError: string | null;
  onRefreshCampus: () => void;
}

export interface MailPageProps extends DashboardPageProps {
  mailboxes: MailboxSummary[];
  inbox: MailInboxSummary | null;
  mailbox: string;
  query: string;
  unreadOnly: boolean;
  mailLoading: boolean;
  mailError: string | null;
  setMailbox: (mailbox: string) => void;
  setQuery: (query: string) => void;
  setUnreadOnly: (unreadOnly: boolean) => void;
  onRefreshMail: () => void;
}

export interface CourseDiscoveryState {
  degrees: string[];
  includePrivate: boolean;
  moduleCodes: string[];
  query: string;
  response: CourseDiscoverySearchResponse | null;
  sources: string[];
  status: CourseDiscoveryStatus | null;
}

export interface CourseDiscoveryPageProps extends DashboardPageProps, CourseNavigationProps {
  discovery: CourseDiscoveryState;
  discoveryError: string | null;
  discoveryLoading: boolean;
  discoverySyncing: boolean;
  onSearchDiscovery: () => Promise<void>;
  onSyncDiscovery: () => Promise<void>;
  setDiscoveryDegrees: (degrees: string[]) => void;
  setDiscoveryIncludePrivate: (includePrivate: boolean) => void;
  setDiscoveryModuleCodes: (moduleCodes: string[]) => void;
  setDiscoveryQuery: (query: string) => void;
  setDiscoverySources: (sources: string[]) => void;
}

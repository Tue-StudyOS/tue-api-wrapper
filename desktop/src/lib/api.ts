import type { AlmaCourseAssignmentsPage, DashboardData, DashboardDocumentReport } from "./dashboard-types";
import type {
  CampusCanteen,
  CampusSnapshot,
  KufTrainingOccupancy,
  SeatAvailabilityResponse,
  UniversityCalendarResponse
} from "./campus-types";
import type { CourseDiscoverySearchResponse, CourseDiscoveryStatus } from "./course-discovery-types";
import type { UnifiedCourseDetail } from "./course-types";
import type { MailboxSummary, MailInboxSummary, MailMessageDetail } from "./mail-types";
import type { DirectoryAction, DirectoryForm, DirectorySearchResponse } from "./people-types";
import type { TimmsItemDetail, TimmsSearchPage, TimmsStreamVariant, TimmsTreePage } from "./timms-types";

export async function fetchDashboard(
  baseUrl: string,
  options: { includeCourseAssignments?: boolean } = {}
): Promise<DashboardData> {
  const params = new URLSearchParams();
  if (options.includeCourseAssignments === false) {
    params.set("include_course_assignments", "false");
  }

  const dashboard = await fetchJson<DashboardData>(baseUrl, `/api/dashboard${params.size ? `?${params}` : ""}`);
  return options.includeCourseAssignments === false ? markCourseAssignmentsPending(dashboard) : dashboard;
}

export async function fetchCourseAssignments(baseUrl: string, term: string): Promise<AlmaCourseAssignmentsPage> {
  const params = new URLSearchParams({ term, limit: "100" });
  return fetchJson<AlmaCourseAssignmentsPage>(baseUrl, `/api/alma/timetable/course-assignments?${params}`);
}

export async function fetchExamReports(baseUrl: string): Promise<DashboardDocumentReport[]> {
  return fetchJson<DashboardDocumentReport[]>(baseUrl, "/api/alma/exams/reports");
}

export function applyCourseAssignments(
  dashboard: DashboardData,
  assignments: AlmaCourseAssignmentsPage
): DashboardData {
  const metrics = dashboard.metrics.filter((metric) => metric.label !== "Saved semester CP");
  metrics.splice(Math.min(1, metrics.length), 0, {
    label: "Saved semester CP",
    value: assignments.total_credits
  });

  return {
    ...dashboard,
    metrics,
    study: {
      ...dashboard.study,
      currentSemesterCredits: assignments.total_credits,
      currentSemesterCreditCourses: assignments.resolved_credit_count,
      currentSemesterCreditUnresolved: assignments.unresolved_credit_summaries,
      currentSemesterCourses: assignments.courses,
      currentSemesterCreditError: null
    }
  };
}

export function markCourseAssignmentsError(dashboard: DashboardData, error: unknown): DashboardData {
  return {
    ...dashboard,
    study: {
      ...dashboard.study,
      currentSemesterCourses: dashboard.study.currentSemesterCourses ?? [],
      currentSemesterCreditError: `Semester credit lookup failed: ${errorMessage("", error).replace(/^: /, "")}`
    }
  };
}

function markCourseAssignmentsPending(dashboard: DashboardData): DashboardData {
  return {
    ...dashboard,
    study: {
      ...dashboard.study,
      currentSemesterCourses: dashboard.study.currentSemesterCourses ?? [],
      currentSemesterCreditError: "Semester credit lookup is loading in the background."
    }
  };
}

export async function fetchCampusSnapshot(baseUrl: string): Promise<CampusSnapshot> {
  const errors: string[] = [];
  const [canteens, events, fitness, seats] = await Promise.all([
    fetchJson<CampusCanteen[]>(baseUrl, "/api/campus/canteens").catch((error) => {
      errors.push(errorMessage("Campus food", error));
      return undefined;
    }),
    fetchJson<UniversityCalendarResponse>(baseUrl, "/api/campus/events?limit=6").catch((error) => {
      errors.push(errorMessage("Campus events", error));
      return undefined;
    }),
    fetchJson<KufTrainingOccupancy>(baseUrl, "/api/campus/fitness/kuf").catch((error) => {
      errors.push(errorMessage("KUF occupancy", error));
      return undefined;
    }),
    fetchJson<SeatAvailabilityResponse>(baseUrl, "/api/campus/seats").catch((error) => {
      errors.push(errorMessage("Library seats", error));
      return undefined;
    })
  ]);

  return {
    canteens,
    events,
    fitness,
    seats,
    errors
  };
}

export async function fetchCourseDetail(
  baseUrl: string,
  input: { title: string; url?: string | null; term?: string | null }
): Promise<UnifiedCourseDetail> {
  const params = new URLSearchParams();
  if (input.url) {
    params.set("url", input.url);
  }
  params.set("title", input.title);
  if (input.term) {
    params.set("term", input.term);
  }
  return fetchJson<UnifiedCourseDetail>(baseUrl, `/api/course-detail?${params.toString()}`);
}

export async function searchCourseDiscovery(
  baseUrl: string,
  input: {
    query: string;
    sources: string[];
    kinds?: string[];
    degrees?: string[];
    moduleCodes?: string[];
    includePrivate: boolean;
    limit?: number;
  }
): Promise<CourseDiscoverySearchResponse> {
  const params = new URLSearchParams({ q: input.query, limit: String(input.limit ?? 20) });
  input.sources.forEach((source) => params.append("source", source));
  input.kinds?.forEach((kind) => params.append("kind", kind));
  input.degrees?.forEach((degree) => params.append("degree", degree));
  input.moduleCodes?.forEach((moduleCode) => params.append("module_code", moduleCode));
  if (input.includePrivate) {
    params.set("include_private", "true");
  }
  return fetchJson<CourseDiscoverySearchResponse>(baseUrl, `/api/discovery/courses/search?${params.toString()}`);
}

export async function fetchCourseDiscoveryStatus(baseUrl: string): Promise<CourseDiscoveryStatus> {
  return fetchJson<CourseDiscoveryStatus>(baseUrl, "/api/discovery/courses/status");
}

export async function refreshCourseDiscoveryIndex(
  baseUrl: string,
  input: { includePrivate: boolean; limit?: number }
): Promise<CourseDiscoveryStatus> {
  const params = new URLSearchParams({
    include_private: String(input.includePrivate),
    limit: String(input.limit ?? 3000)
  });
  return fetchJson<CourseDiscoveryStatus>(baseUrl, `/api/discovery/courses/refresh?${params.toString()}`, {
    method: "POST"
  });
}

export async function fetchMailboxes(baseUrl: string): Promise<MailboxSummary[]> {
  return fetchJson<MailboxSummary[]>(baseUrl, "/api/mail/mailboxes");
}

export async function fetchMailInbox(
  baseUrl: string,
  options: { mailbox: string; unreadOnly: boolean; query: string }
): Promise<MailInboxSummary> {
  const params = new URLSearchParams({
    mailbox: options.mailbox,
    limit: "30",
    unread_only: String(options.unreadOnly)
  });
  if (options.query.trim()) {
    params.set("query", options.query.trim());
  }
  return fetchJson<MailInboxSummary>(baseUrl, `/api/mail/inbox?${params.toString()}`);
}

export async function fetchMailMessage(
  baseUrl: string,
  input: { uid: string; mailbox: string }
): Promise<MailMessageDetail> {
  const params = new URLSearchParams({ mailbox: input.mailbox });
  return fetchJson<MailMessageDetail>(baseUrl, `/api/mail/messages/${encodeURIComponent(input.uid)}?${params}`);
}

export async function moveMailMessage(
  baseUrl: string,
  input: { uid: string; mailbox: string; destination: string }
): Promise<void> {
  await fetchJson(baseUrl, `/api/mail/messages/${encodeURIComponent(input.uid)}/move`, {
    method: "POST",
    body: JSON.stringify({ mailbox: input.mailbox, destination: input.destination })
  });
}

export async function searchTimms(baseUrl: string, query: string): Promise<TimmsSearchPage> {
  return fetchJson<TimmsSearchPage>(baseUrl, `/api/timms/search?query=${encodeURIComponent(query)}&limit=12`);
}

export async function fetchTimmsItem(baseUrl: string, itemId: string): Promise<TimmsItemDetail> {
  return fetchJson<TimmsItemDetail>(baseUrl, `/api/timms/items/${encodeURIComponent(itemId)}`);
}

export async function fetchTimmsStreams(baseUrl: string, itemId: string): Promise<TimmsStreamVariant[]> {
  return fetchJson<TimmsStreamVariant[]>(baseUrl, `/api/timms/items/${encodeURIComponent(itemId)}/streams`);
}

export async function fetchTimmsTree(
  baseUrl: string,
  input: { nodeId?: string | null; nodePath?: string | null } = {}
): Promise<TimmsTreePage> {
  const params = new URLSearchParams();
  if (input.nodeId) {
    params.set("node_id", input.nodeId);
  }
  if (input.nodePath) {
    params.set("node_path", input.nodePath);
  }
  return fetchJson<TimmsTreePage>(baseUrl, `/api/timms/tree${params.size ? `?${params.toString()}` : ""}`);
}

export async function searchPeople(baseUrl: string, query: string): Promise<DirectorySearchResponse> {
  return fetchJson<DirectorySearchResponse>(baseUrl, `/api/people/search?query=${encodeURIComponent(query)}`);
}

export async function submitPeopleAction(
  baseUrl: string,
  input: { query: string; form: DirectoryForm; action: DirectoryAction }
): Promise<DirectorySearchResponse> {
  return fetchJson<DirectorySearchResponse>(baseUrl, "/api/people/action", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function fetchJson<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    cache: "no-store",
    headers: init?.body ? { "Content-Type": "application/json", ...init.headers } : init?.headers,
    ...init
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(readErrorDetail(detail) || `Request failed with ${response.status}.`);
  }

  return (await response.json()) as T;
}

function readErrorDetail(payload: string): string | null {
  if (!payload) {
    return null;
  }
  try {
    const parsed = JSON.parse(payload) as { detail?: unknown };
    return typeof parsed.detail === "string" ? parsed.detail : payload;
  } catch {
    return payload;
  }
}

function errorMessage(scope: string, error: unknown): string {
  return `${scope}: ${error instanceof Error ? error.message : "Request failed."}`;
}

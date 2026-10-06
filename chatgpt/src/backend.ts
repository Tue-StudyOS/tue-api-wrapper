import type {
  AlmaCourseSearchFiltersPayload,
  AlmaCourseSearchResponse,
  AlmaExamRecord,
  AlmaStudyPlannerPayload,
  AuthenticatedCourseSearchResponse,
  AlmaTimetablePayload,
  DashboardPayload,
  DocumentsSummaryPayload,
  IliasContentPage,
  IliasExerciseAssignment,
  IliasForumTopic,
  IliasSearchResponse,
  IliasMembershipItem,
  LearningSpaceInspection,
  MailInboxResponse,
  MailMessageDetailResponse,
  IliasTaskItem,
  ModuleDetail,
  SearchItem
} from "./types.js";
import { normalizeOptionalStudyTerm, normalizeStudyTerm } from "./terms.js";

import { buildPortalApiUrl, fetchPortalJson as fetchJson, PortalBackendError } from "./backend-http.js";
export { buildPortalApiUrl, PortalBackendError } from "./backend-http.js";

function buildQueryString(params: Record<string, string | number | readonly string[] | undefined>): string {
  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        if (item.trim()) {
          query.append(key, item);
        }
      }
      continue;
    }

    query.set(key, String(value));
  }

  const suffix = query.toString();
  return suffix ? `?${suffix}` : "";
}
function normalizeDashboard(dashboard: DashboardPayload): DashboardPayload {
  return {
    ...dashboard,
    documents: {
      ...dashboard.documents,
      currentDownloadUrl: dashboard.documents.currentDownloadUrl
        ? buildPortalApiUrl(dashboard.documents.currentDownloadUrl)
        : null
    }
  };
}
function normalizeDocumentsSummary(documents: DocumentsSummaryPayload): DocumentsSummaryPayload {
  return {
    ...documents,
    currentDownloadUrl: documents.currentDownloadUrl
      ? buildPortalApiUrl(documents.currentDownloadUrl)
      : null,
  };
}

export interface CourseCatalogSearchParams {
  query?: string;
  title?: string;
  number?: string;
  elementType?: readonly string[];
  language?: readonly string[];
  degree?: readonly string[];
  subject?: readonly string[];
  faculty?: readonly string[];
  maxResults?: number;
}

export interface CourseOfferingSearchParams {
  query?: string;
  term?: string;
  limit?: number;
}

export interface MailInboxParams {
  mailbox?: string;
  limit?: number;
  query?: string;
  sender?: string;
  unreadOnly?: boolean;
}

export interface LearningSpaceSearchParams {
  term: string;
  page?: number;
  searchMode?: string;
  contentType?: readonly string[];
  createdEnabled?: boolean;
  createdMode?: string;
  createdDate?: string;
}
export async function loadDashboard(term = normalizeStudyTerm(undefined), limit = 8): Promise<DashboardPayload> {
  const dashboard = await fetchJson<DashboardPayload>(
    `/api/dashboard?term=${encodeURIComponent(normalizeStudyTerm(term))}&limit=${limit}`
  );
  return normalizeDashboard(dashboard);
}

export async function loadTasks(limit = 8): Promise<IliasTaskItem[]> {
  return fetchJson<IliasTaskItem[]>(`/api/ilias/tasks?limit=${limit}`);
}

export async function loadMemberships(limit = 8): Promise<IliasMembershipItem[]> {
  return fetchJson<IliasMembershipItem[]>(`/api/ilias/memberships?limit=${limit}`);
}

export async function loadExams(limit = 8): Promise<AlmaExamRecord[]> {
  return fetchJson<AlmaExamRecord[]>(`/api/alma/exams?limit=${limit}`);
}

export async function loadTimetable(term = normalizeStudyTerm(undefined)): Promise<AlmaTimetablePayload> {
  return fetchJson<AlmaTimetablePayload>(`/api/alma/timetable?term=${encodeURIComponent(normalizeStudyTerm(term))}`);
}

export async function loadEnrollments(): Promise<DashboardPayload["enrollment"]> {
  return fetchJson<DashboardPayload["enrollment"]>("/api/alma/enrollments");
}

export async function loadDocumentsSummary(): Promise<DocumentsSummaryPayload> {
  const documents = await fetchJson<DocumentsSummaryPayload>("/api/alma/studyservice/summary");
  return normalizeDocumentsSummary(documents);
}

export async function loadStudyPlanner(): Promise<AlmaStudyPlannerPayload> {
  return fetchJson<AlmaStudyPlannerPayload>("/api/alma/study-planner");
}

export async function loadCourseCatalogFilters(): Promise<AlmaCourseSearchFiltersPayload> {
  return fetchJson<AlmaCourseSearchFiltersPayload>("/api/alma/module-search/filters");
}

export async function searchCourseCatalog(
  params: CourseCatalogSearchParams
): Promise<AlmaCourseSearchResponse> {
  const query = buildQueryString({
    query: params.query?.trim(),
    title: params.title?.trim(),
    number: params.number?.trim(),
    element_type: params.elementType,
    language: params.language,
    degree: params.degree,
    subject: params.subject,
    faculty: params.faculty,
    max_results: params.maxResults ?? 10
  });

  return fetchJson<AlmaCourseSearchResponse>(`/api/alma/module-search${query}`);
}

export async function searchCourseOfferings(
  params: CourseOfferingSearchParams
): Promise<AuthenticatedCourseSearchResponse> {
  const query = buildQueryString({
    query: params.query?.trim(),
    term: normalizeOptionalStudyTerm(params.term),
    limit: params.limit ?? 12,
  });

  return fetchJson<AuthenticatedCourseSearchResponse>(`/api/alma/course-search${query}`);
}

export async function loadCourseDetail(url: string): Promise<ModuleDetail> {
  return fetchJson<ModuleDetail>(`/api/alma/module-detail?url=${encodeURIComponent(url)}`);
}

export async function loadMailInbox(params: MailInboxParams = {}): Promise<MailInboxResponse> {
  const query = buildQueryString({
    mailbox: params.mailbox?.trim(),
    limit: params.limit ?? 8,
    query: params.query?.trim(),
    sender: params.sender?.trim(),
    unread_only: params.unreadOnly ? "true" : undefined,
  });

  return fetchJson<MailInboxResponse>(`/api/mail/inbox${query}`);
}

export async function loadMailMessage(
  uid: string,
  mailbox = "INBOX",
): Promise<MailMessageDetailResponse> {
  return fetchJson<MailMessageDetailResponse>(
    `/api/mail/messages/${encodeURIComponent(uid)}?mailbox=${encodeURIComponent(mailbox)}`,
  );
}

export async function searchLearningSpaces(
  params: LearningSpaceSearchParams
): Promise<IliasSearchResponse> {
  const query = buildQueryString({
    term: params.term.trim(),
    page: params.page ?? 1,
    search_mode: params.searchMode?.trim(),
    content_type: params.contentType,
    created_enabled: params.createdEnabled ? "true" : undefined,
    created_mode: params.createdMode?.trim(),
    created_date: params.createdDate?.trim(),
  });

  return fetchJson<IliasSearchResponse>(`/api/ilias/search${query}`);
}

export async function inspectLearningSpace(target: string): Promise<LearningSpaceInspection> {
  const encodedTarget = encodeURIComponent(target);
  const [contentResult, forumResult, exerciseResult] = await Promise.allSettled([
    fetchJson<IliasContentPage>(`/api/ilias/content?target=${encodedTarget}`),
    fetchJson<IliasForumTopic[]>(`/api/ilias/forum?target=${encodedTarget}`),
    fetchJson<IliasExerciseAssignment[]>(`/api/ilias/exercise?target=${encodedTarget}`),
  ]);

  const content = contentResult.status === "fulfilled" ? contentResult.value : null;
  const forum = forumResult.status === "fulfilled" ? forumResult.value : [];
  const exercise = exerciseResult.status === "fulfilled" ? exerciseResult.value : [];

  if (!content && !forum.length && !exercise.length) {
    const primaryError = contentResult.status === "rejected"
      ? contentResult.reason
      : forumResult.status === "rejected"
        ? forumResult.reason
        : exerciseResult.status === "rejected"
          ? exerciseResult.reason
          : null;

    if (primaryError instanceof PortalBackendError) {
      throw primaryError;
    }
    throw new PortalBackendError("No learning-space data was returned for the requested target.");
  }

  return {
    content,
    forum,
    exercise,
    errors: Object.fromEntries(
      [["content", contentResult], ["forum", forumResult], ["exercise", exerciseResult]]
        .flatMap(([name, result]) => {
          const settled = result as PromiseSettledResult<unknown>;
          return settled.status === "rejected"
            ? [[name, settled.reason instanceof PortalBackendError ? settled.reason.message : "This section could not be loaded."]]
            : [];
        }),
    ),
  };
}

export async function searchItems(query: string): Promise<SearchItem[]> {
  const response = await fetchJson<{ results: SearchItem[] }>(
    `/api/search?query=${encodeURIComponent(query)}`
  );

  return response.results;
}

export async function fetchItem(id: string): Promise<SearchItem> {
  return fetchJson(`/api/items/${encodeURIComponent(id)}`);
}

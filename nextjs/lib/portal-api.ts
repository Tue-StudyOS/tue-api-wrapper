import type {
  IliasContentPage,
  IliasExerciseAssignment,
  IliasForumTopic,
  IliasMembershipItem,
  IliasTaskItem,
  MailInboxResponse,
  MailInboxFilters,
  MailMessageDetailResponse,
  MailboxSummary,
  ModuleDetail,
  DashboardData,
  DocumentsPanel,
  EnrollmentState,
  ExamItem,
  ModuleSearchFiltersResponse,
  ModuleSearchResponse,
  MoodleCalendarData,
  MoodleCategoryPage,
  MoodleCourseDetail,
  MoodleCoursesResponse,
  MoodleDashboardData,
  MoodleGradesResponse,
  MoodleMessagesResponse,
  MoodleNotificationsResponse,
  PortalLink
} from "./types";
import type {
  AlmaCourseCatalogPage,
  AlmaCourseSearchResponse,
  AlmaDocumentReport,
  AlmaPortalMessagesFeed,
  AlmaStudyPlannerResponse,
  AlmaTimetableExportLink,
  AlmaTimetableView,
  IliasActionResult,
  IliasSearchFilters,
  IliasSearchResponse,
  IliasWaitlistResult,
  IliasWaitlistSupport
} from "./discovery-types";

const apiBaseUrl = process.env.PORTAL_API_BASE_URL ?? "http://127.0.0.1:8000";

export function buildPortalApiUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${apiBaseUrl}${path}`;
}

export class PortalApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PortalApiError";
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      cache: "no-store",
      ...init
    });
  } catch (error) {
    throw new PortalApiError(
      `Could not reach the backend at ${apiBaseUrl}. Start the Python API or set PORTAL_API_BASE_URL correctly.`
    );
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new PortalApiError(
      `Backend request failed for ${path} with ${response.status}${detail ? `: ${detail}` : ""}`
    );
  }

  return (await response.json()) as T;
}

export function getDashboard(): Promise<DashboardData> {
  return fetchJson("/api/dashboard");
}

export function getDocuments(): Promise<DocumentsPanel> {
  return fetchJson("/api/alma/studyservice/summary");
}

export function getMailMailboxes(): Promise<MailboxSummary[]> {
  return fetchJson("/api/mail/mailboxes");
}

export function getMailInbox(filters: Partial<MailInboxFilters> = {}): Promise<MailInboxResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(filters.limit ?? 12));
  if (filters.mailbox?.trim()) {
    params.set("mailbox", filters.mailbox.trim());
  }
  if (filters.query?.trim()) {
    params.set("query", filters.query.trim());
  }
  if (filters.sender?.trim()) {
    params.set("sender", filters.sender.trim());
  }
  if (filters.unreadOnly) {
    params.set("unread_only", "true");
  }
  return fetchJson(`/api/mail/inbox?${params.toString()}`);
}

export function getMailMessage(uid: string, mailbox = "INBOX"): Promise<MailMessageDetailResponse> {
  return fetchJson(`/api/mail/messages/${encodeURIComponent(uid)}?mailbox=${encodeURIComponent(mailbox)}`);
}

export function getAlmaExams(limit = 20): Promise<ExamItem[]> {
  return fetchJson(`/api/alma/exams?limit=${limit}`);
}

export function getAlmaEnrollment(): Promise<EnrollmentState> {
  return fetchJson("/api/alma/enrollments");
}

export function getAlmaStudyPlanner(): Promise<AlmaStudyPlannerResponse> {
  return fetchJson("/api/alma/study-planner");
}

export function getAlmaTimetableView({
  term = "",
  week = "",
  fromDate = "",
  toDate = "",
  singleDay = "",
  limit = 200
}: {
  term?: string;
  week?: string;
  fromDate?: string;
  toDate?: string;
  singleDay?: string;
  limit?: number;
} = {}): Promise<AlmaTimetableView> {
  const params = new URLSearchParams();
  if (term.trim()) {
    params.set("term", term.trim());
  }
  if (week.trim()) {
    params.set("week", week.trim());
  }
  if (fromDate.trim()) {
    params.set("from_date", fromDate.trim());
  }
  if (toDate.trim()) {
    params.set("to_date", toDate.trim());
  }
  if (singleDay.trim()) {
    params.set("single_day", singleDay.trim());
  }
  params.set("limit", String(limit));
  return fetchJson(`/api/alma/timetable/view?${params.toString()}`);
}

export function refreshAlmaTimetableExportUrl(term = ""): Promise<AlmaTimetableExportLink> {
  const params = new URLSearchParams();
  if (term.trim()) {
    params.set("term", term.trim());
  }
  return fetchJson(`/api/alma/timetable/export-url/refresh?${params.toString()}`, {
    method: "POST"
  });
}

export function buildAlmaTimetablePdfUrl({
  term = "",
  week = "",
  fromDate = "",
  toDate = "",
  singleDay = ""
}: {
  term?: string;
  week?: string;
  fromDate?: string;
  toDate?: string;
  singleDay?: string;
} = {}): string {
  const params = new URLSearchParams();
  if (term.trim()) params.set("term", term.trim());
  if (week.trim()) params.set("week", week.trim());
  if (fromDate.trim()) params.set("from_date", fromDate.trim());
  if (toDate.trim()) params.set("to_date", toDate.trim());
  if (singleDay.trim()) params.set("single_day", singleDay.trim());
  const query = params.toString();
  return buildPortalApiUrl(`/api/alma/timetable/pdf${query ? `?${query}` : ""}`);
}

export function getAlmaPortalMessagesFeed(): Promise<AlmaPortalMessagesFeed> {
  return fetchJson("/api/alma/portal-messages/feed");
}

export function getAlmaExamReports(): Promise<AlmaDocumentReport[]> {
  return fetchJson("/api/alma/exams/reports");
}

export function refreshAlmaPortalMessagesFeed(): Promise<AlmaPortalMessagesFeed> {
  return fetchJson("/api/alma/portal-messages/feed/refresh", {
    method: "POST"
  });
}

export function getAlmaCourseSearch({
  query = "",
  term = "",
  limit = 20
}: {
  query?: string;
  term?: string;
  limit?: number;
} = {}): Promise<AlmaCourseSearchResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("query", query.trim());
  }
  if (term.trim()) {
    params.set("term", term.trim());
  }
  params.set("limit", String(limit));
  return fetchJson(`/api/alma/course-search?${params.toString()}`);
}

export function getAlmaCourseCatalogPage({
  term = "",
  limit = 80
}: {
  term?: string;
  limit?: number;
} = {}): Promise<AlmaCourseCatalogPage> {
  const params = new URLSearchParams();
  if (term.trim()) {
    params.set("term", term.trim());
  }
  params.set("limit", String(limit));
  return fetchJson(`/api/alma/catalog/page?${params.toString()}`);
}

export async function getIliasLinks(): Promise<PortalLink[]> {
  const data = await fetchJson<{
    mainbar_links: PortalLink[];
    top_categories: PortalLink[];
  }>("/api/ilias/root");

  return [...data.mainbar_links, ...data.top_categories];
}

export function getIliasContent(target: string): Promise<IliasContentPage> {
  return fetchJson(`/api/ilias/content?target=${encodeURIComponent(target)}`);
}

export function getIliasForum(target: string): Promise<IliasForumTopic[]> {
  return fetchJson(`/api/ilias/forum?target=${encodeURIComponent(target)}`);
}

export function getIliasExercise(target: string): Promise<IliasExerciseAssignment[]> {
  return fetchJson(`/api/ilias/exercise?target=${encodeURIComponent(target)}`);
}

export function getIliasMemberships(limit = 20): Promise<IliasMembershipItem[]> {
  return fetchJson(`/api/ilias/memberships?limit=${limit}`);
}

export function getIliasSearchOptions(): Promise<IliasSearchFilters> {
  return fetchJson("/api/ilias/search/options");
}

export function searchIlias({
  term,
  page = 1,
  searchMode = "",
  contentTypes = [],
  createdEnabled = false,
  createdMode = "",
  createdDate = ""
}: {
  term: string;
  page?: number;
  searchMode?: string;
  contentTypes?: string[];
  createdEnabled?: boolean;
  createdMode?: string;
  createdDate?: string;
}): Promise<IliasSearchResponse> {
  const params = new URLSearchParams();
  params.set("term", term.trim());
  params.set("page", String(page));
  if (searchMode.trim()) {
    params.set("search_mode", searchMode.trim());
  }
  for (const value of contentTypes) {
    params.append("content_type", value);
  }
  if (createdEnabled) {
    params.set("created_enabled", "true");
  }
  if (createdMode.trim()) {
    params.set("created_mode", createdMode.trim());
  }
  if (createdDate.trim()) {
    params.set("created_date", createdDate.trim());
  }
  return fetchJson(`/api/ilias/search?${params.toString()}`);
}

export function addIliasFavorite(url: string): Promise<IliasActionResult> {
  return fetchJson(`/api/ilias/favorites?url=${encodeURIComponent(url)}`, {
    method: "POST"
  });
}

export function getIliasWaitlistSupport(url: string): Promise<IliasWaitlistSupport> {
  return fetchJson(`/api/ilias/waitlist/support?url=${encodeURIComponent(url)}`);
}

export function joinIliasWaitlist({
  url,
  acceptAgreement = false
}: {
  url: string;
  acceptAgreement?: boolean;
}): Promise<IliasWaitlistResult> {
  const params = new URLSearchParams();
  params.set("url", url);
  if (acceptAgreement) {
    params.set("accept_agreement", "true");
  }
  return fetchJson(`/api/ilias/waitlist/join?${params.toString()}`, {
    method: "POST"
  });
}

export function getIliasTasks(limit = 20): Promise<IliasTaskItem[]> {
  return fetchJson(`/api/ilias/tasks?limit=${limit}`);
}

export function getModuleSearchFilters(): Promise<ModuleSearchFiltersResponse> {
  return fetchJson("/api/alma/module-search/filters");
}

export function getModuleDetail(url: string): Promise<ModuleDetail> {
  return fetchJson(`/api/alma/module-detail?url=${encodeURIComponent(url)}`);
}

export function getMoodleDashboard(): Promise<MoodleDashboardData> {
  return fetchJson("/api/moodle/dashboard");
}

export function getMoodleCalendar(days = 30, limit = 50): Promise<MoodleCalendarData> {
  return fetchJson(`/api/moodle/calendar?days=${days}&limit=${limit}`);
}

export function getMoodleCourses(limit = 24, offset = 0): Promise<MoodleCoursesResponse> {
  return fetchJson(`/api/moodle/courses?limit=${limit}&offset=${offset}`);
}

export function getMoodleCategories(categoryId?: number): Promise<MoodleCategoryPage> {
  if (categoryId === undefined) {
    return fetchJson("/api/moodle/categories");
  }
  return fetchJson(`/api/moodle/categories/${categoryId}`);
}

export function getMoodleCourseDetail(courseId: number): Promise<MoodleCourseDetail> {
  return fetchJson(`/api/moodle/course/${courseId}`);
}

export function getMoodleGrades(limit = 50): Promise<MoodleGradesResponse> {
  return fetchJson(`/api/moodle/grades?limit=${limit}`);
}

export function getMoodleMessages(limit = 20): Promise<MoodleMessagesResponse> {
  return fetchJson(`/api/moodle/messages?limit=${limit}`);
}

export function getMoodleNotifications(limit = 20): Promise<MoodleNotificationsResponse> {
  return fetchJson(`/api/moodle/notifications?limit=${limit}`);
}

export function buildAlmaDocumentUrl(docId: string): string {
  return buildPortalApiUrl(`/api/alma/documents/${encodeURIComponent(docId)}`);
}

export async function searchModules({
  query = "",
  title = "",
  number = "",
  elementTypes = [],
  languages = [],
  degrees = [],
  subjects = [],
  faculties = [],
  maxResults = 100
}: {
  query?: string;
  title?: string;
  number?: string;
  elementTypes?: string[];
  languages?: string[];
  degrees?: string[];
  subjects?: string[];
  faculties?: string[];
  maxResults?: number;
}): Promise<ModuleSearchResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("query", query.trim());
  }
  if (title.trim()) {
    params.set("title", title.trim());
  }
  if (number.trim()) {
    params.set("number", number.trim());
  }
  for (const value of elementTypes) {
    params.append("element_type", value);
  }
  for (const value of languages) {
    params.append("language", value);
  }
  for (const value of degrees) {
    params.append("degree", value);
  }
  for (const value of subjects) {
    params.append("subject", value);
  }
  for (const value of faculties) {
    params.append("faculty", value);
  }
  params.set("max_results", String(maxResults));

  return fetchJson(`/api/alma/module-search?${params.toString()}`);
}

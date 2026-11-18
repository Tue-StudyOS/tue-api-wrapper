import type { TalksPanel } from "./dashboard-talk-types";

export interface Metric {
  label: string;
  value: number;
}

export interface CalendarRoomDetails {
  room_default: string | null;
  room_short: string | null;
  room_long: string | null;
  floor_default: string | null;
  floor_short: string | null;
  floor_long: string | null;
  building_default: string | null;
  building_short: string | null;
  building_long: string | null;
  campus_default: string | null;
  campus_short: string | null;
  campus_long: string | null;
  detail_url: string | null;
  display_text: string | null;
}

export interface AgendaItem {
  summary: string;
  start: string;
  end: string | null;
  location: string | null;
  description: string | null;
  room_details?: CalendarRoomDetails | null;
  status?: "cancelled" | null;
  cancellation_reason?: string | null;
}

export interface DocumentReport {
  label: string;
  trigger_name: string;
}

export interface StudyServiceTab {
  button_name: string;
  label: string;
  is_active: boolean;
}

export interface StudyServiceOutputRequest {
  trigger_name: string;
  label: string;
  count: number | null;
  message: string | null;
}

export interface DocumentsPanel {
  bannerText: string | null;
  personName: string | null;
  activeTabLabel: string | null;
  tabs: StudyServiceTab[];
  outputRequests: StudyServiceOutputRequest[];
  reports: DocumentReport[];
  currentDownloadAvailable: boolean;
  currentDownloadUrl: string | null;
  sourcePageUrl: string;
}

export interface MailMessageSummary {
  uid: string;
  subject: string;
  from_name: string | null;
  from_address: string | null;
  received_at: string | null;
  preview: string | null;
  is_unread: boolean;
}

export interface MailInboxResponse {
  account: string;
  mailbox: string;
  unread_count: number;
  messages: MailMessageSummary[];
}

export interface MailMessageDetailResponse {
  uid: string;
  mailbox: string;
  subject: string;
  from_name: string | null;
  from_address: string | null;
  to_recipients: string[];
  cc_recipients: string[];
  received_at: string | null;
  preview: string | null;
  body_text: string | null;
  attachment_names: string[];
  is_unread: boolean;
}

export interface MailboxSummary {
  name: string;
  label: string;
  special_use: string | null;
  message_count: number | null;
  unread_count: number | null;
}

export interface MailInboxFilters {
  mailbox: string;
  query: string;
  sender: string;
  unreadOnly: boolean;
  limit: number;
}

export interface MailPanel {
  available: boolean;
  account: string | null;
  mailbox: string;
  unreadCount: number;
  items: MailMessageSummary[];
  error: string | null;
}

export interface CatalogNode {
  level: number;
  kind: string | null;
  title: string;
  description: string | null;
  permalink: string | null;
  expandable: boolean;
}

export interface CatalogPanel {
  nodes: CatalogNode[];
  sourcePageUrl: string;
}

export interface ExamItem {
  level: number;
  kind: string | null;
  title: string;
  number: string | null;
  attempt: string | null;
  grade: string | null;
  cp: string | null;
  status: string | null;
}

export interface PortalLink {
  label: string;
  url: string;
}

export interface QuickLink {
  label: string;
  href: string;
  description: string;
}

export interface ModuleSearchResult {
  number: string | null;
  title: string;
  element_type: string | null;
  detail_url: string | null;
}

export interface SearchOption {
  value: string;
  label: string;
}

export interface ModuleSearchFiltersResponse {
  sourcePageUrl: string;
  filters: {
    elementTypes: SearchOption[];
    languages: SearchOption[];
    degrees: SearchOption[];
    subjects: SearchOption[];
    faculties: SearchOption[];
  };
}

export interface ModuleSearchResponse {
  results: ModuleSearchResult[];
  returnedResults: number;
  totalResults: number | null;
  totalPages: number | null;
  truncated: boolean;
  sourcePageUrl: string;
}

export interface AlmaDetailField {
  label: string;
  value: string;
}

export interface AlmaDetailSection {
  title: string;
  fields: AlmaDetailField[];
}

export interface AlmaDetailTable {
  title: string;
  headers: string[];
  rows: string[][];
}

export interface ModuleDetail {
  title: string;
  number: string | null;
  permalink: string | null;
  source_url: string;
  active_tab: string | null;
  available_tabs: string[];
  sections: AlmaDetailSection[];
  module_study_program_tables: AlmaDetailTable[];
}

export interface IliasContentItem {
  label: string;
  url: string;
  kind: string | null;
  properties: string[];
}

export interface IliasContentSection {
  label: string;
  items: IliasContentItem[];
}

export interface IliasContentPage {
  title: string;
  page_url: string;
  sections: IliasContentSection[];
}

export interface IliasForumTopic {
  title: string;
  url: string;
  author: string | null;
  posts: string | null;
  last_post: string | null;
  visits: string | null;
}

export interface IliasExerciseAssignment {
  title: string;
  url: string;
  due_hint: string | null;
  due_at: string | null;
  requirement: string | null;
  last_submission: string | null;
  submission_type: string | null;
  status: string | null;
  team_action_url: string | null;
}

export interface EnrollmentState {
  selected_term: string | null;
  available_terms: Record<string, string>;
  message: string | null;
}

export interface StudySummary {
  selectedTerm: string | null;
  message: string | null;
  passedExamCount: number;
  trackedCredits: number;
  currentSemesterCredits: number | null;
  currentSemesterCreditCourses: number;
  currentSemesterCreditUnresolved: string[];
  currentSemesterCreditError: string | null;
  availableTerms: Record<string, string>;
}

export interface IliasMembershipItem {
  title: string;
  url: string;
  kind: string | null;
  description: string | null;
  info_url: string | null;
  properties: string[];
}

export interface IliasTaskItem {
  title: string;
  url: string;
  item_type: string | null;
  start: string | null;
  end: string | null;
}

export interface MoodleDashboardEvent {
  id: number | null;
  title: string;
  due_at: string | null;
  formatted_time: string | null;
  course_name: string | null;
  course_id: number | null;
  action_url: string | null;
  description: string | null;
  is_actionable: boolean;
}

export interface MoodleRecentItem {
  id: number | null;
  title: string;
  item_type: string | null;
  course_name: string | null;
  course_id: number | null;
  url: string | null;
  icon_url: string | null;
}

export interface MoodleCourseSummary {
  id: number | null;
  title: string;
  shortname: string | null;
  category_name: string | null;
  visible: boolean | null;
  end_date: string | null;
  url: string | null;
  image_url: string | null;
  summary?: string | null;
  teachers?: string[];
}

export interface MoodleDashboardData {
  source_url: string;
  events: MoodleDashboardEvent[];
  recent_items: MoodleRecentItem[];
  courses: MoodleCourseSummary[];
}

export interface MoodleCalendarData {
  source_url: string;
  from_timestamp: number;
  to_timestamp: number;
  items: MoodleDashboardEvent[];
}

export interface MoodleCoursesResponse {
  source_url: string;
  items: MoodleCourseSummary[];
  next_offset: number | null;
}

export interface MoodleCategorySummary {
  id: number | null;
  title: string;
  url: string;
  description: string | null;
  course_count: number | null;
}

export interface MoodleCategoryPage {
  category_id: number | null;
  title: string;
  source_url: string;
  categories: MoodleCategorySummary[];
  courses: MoodleCourseSummary[];
}

export interface MoodleCourseDetail {
  id: number | null;
  title: string;
  source_url: string;
  course_url: string | null;
  summary: string | null;
  teachers: string[];
  self_enrolment_available: boolean;
  requires_enrolment_key: boolean;
  enrolment_label: string | null;
  enrolment_action_url: string | null;
  enrolment_payload: Record<string, string>;
  enrolment_key_field_name: string | null;
}

export interface MoodleGradeItem {
  course_title: string;
  grade: string | null;
  percentage: string | null;
  range_hint: string | null;
  rank: string | null;
  feedback: string | null;
  url: string | null;
}

export interface MoodleGradesResponse {
  source_url: string;
  items: MoodleGradeItem[];
}

export interface MoodleMessageItem {
  title: string;
  preview: string | null;
  sender: string | null;
  timestamp: string | null;
  url: string | null;
  unread: boolean | null;
}

export interface MoodleMessagesResponse {
  source_url: string;
  items: MoodleMessageItem[];
}

export interface MoodleNotificationItem {
  title: string;
  body: string | null;
  timestamp: string | null;
  url: string | null;
  unread: boolean | null;
}

export interface MoodleNotificationsResponse {
  source_url: string;
  items: MoodleNotificationItem[];
}

export interface DashboardData {
  generatedAt: string;
  termLabel: string;
  hero: {
    title: string;
    subtitle: string;
  };
  metrics: Metric[];
  agenda: {
    exportUrl: string;
    items: AgendaItem[];
  };
  study: StudySummary;
  documents: DocumentsPanel;
  exams: ExamItem[];
  enrollment: EnrollmentState;
  ilias: {
    title: string;
    mainbarLinks: PortalLink[];
    topCategories: PortalLink[];
    memberships: IliasMembershipItem[];
    tasks: IliasTaskItem[];
  };
  mail: MailPanel;
  talks: TalksPanel;
  quickLinks: QuickLink[];
}

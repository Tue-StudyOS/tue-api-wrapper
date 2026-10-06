import { z } from "zod";

const record = z.object({}).passthrough();
const records = z.array(record);
const nullableText = z.string().nullable();
const searchItem = z.object({ id: z.string(), title: z.string(), url: z.string(), text: z.string() }).passthrough();
const study = z.object({ passedExamCount: z.number(), trackedCredits: z.number(), currentSemesterCredits: z.number().nullable() }).passthrough();
const documents = z.object({ reports: records, currentDownloadAvailable: z.boolean(), currentDownloadUrl: nullableText }).passthrough();
const detail = z.object({ title: z.string(), source_url: z.string(), sections: records, module_study_program_tables: records }).passthrough();
const intent = z.object({ id: z.string(), kind: z.string(), title: z.string(), actionLabel: z.string(), expiresAt: z.string() }).passthrough();
const prepared = { view: z.literal("critical-action"), intent };

// Validate stable output fields while retaining additional upstream contract fields.
const successShapes: Record<string, z.ZodRawShape> = {
  search: { results: z.array(searchItem) },
  fetch: { item: searchItem },
  get_study_snapshot: {
    generatedAt: z.string(), termLabel: z.string(), study,
    metrics: records, nextEvents: records, openTasks: records, grades: records, learningSpaces: records, documents: record,
  },
  get_upcoming_schedule: { termLabel: z.string(), exportUrl: z.string(), items: records },
  get_current_tasks: { tasks: records },
  get_current_grades: { study, exams: records },
  get_learning_spaces: { memberships: records },
  get_documents_summary: documents.shape,
  get_mensa_food_plan: {
    view: z.literal("mensa"), date: z.string(), canteens: records, matched_menu_count: z.number().int().nonnegative(),
    requested_canteen_ids: z.array(z.string()), requested_icons: z.array(z.string()),
  },
  get_mail_inbox: { account: z.string(), mailbox: z.string(), unread_count: z.number(), messages: records },
  get_mail_message: { uid: z.string(), mailbox: z.string(), subject: z.string(), body_text: nullableText, attachment_names: z.array(z.string()) },
  get_course_catalog_filters: { sourcePageUrl: z.string(), filters: record },
  search_courses: { results: records, returnedResults: z.number(), totalResults: z.number().nullable(), sourcePageUrl: z.string() },
  search_course_offerings: { query: z.string(), page_url: z.string(), results: records },
  get_course_detail: detail.shape,
  get_combined_course_detail: { alma: detail, ilias_results: records, portal_statuses: records, registration_hints: records },
  get_study_planner: { title: z.string(), page_url: z.string(), semesters: records, modules: records, view_state: record },
  search_learning_spaces: { page_url: z.string(), query: z.string(), page_number: z.number(), results: records },
  inspect_learning_space: { content: record.nullable(), forum: records, exercise: records, errors: z.record(z.string()) },
  show_dashboard: { view: z.literal("dashboard"), dashboard: z.object({ generatedAt: z.string(), termLabel: z.string(), study }).passthrough() },
  list_documents: { view: z.literal("documents"), documents },
  prepare_alma_course_registration: prepared,
  prepare_ilias_waitlist_join: prepared,
  prepare_ilias_add_favorite: prepared,
  prepare_moodle_course_enrolment: prepared,
  confirm_critical_action: { status: z.literal("completed"), kind: z.string(), intent, result: z.object({ status: z.string(), message: nullableText, finalUrl: nullableText }).passthrough() },
  cancel_critical_action: { status: z.literal("cancelled") },
};

export const outputSchemas = Object.fromEntries(
  Object.entries(successShapes).map(([name, shape]) => [name, z.object(shape).passthrough()]),
);

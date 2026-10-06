import { PortalBackendError, fetchPortalJson as fetchJson } from "./backend-http.js";
import type { CriticalActionResult } from "./types/actions.js";

function queryString(params: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const suffix = query.toString();
  return suffix ? `?${suffix}` : "";
}

function actionResult(raw: Record<string, unknown>): CriticalActionResult {
  if (raw.success === false || raw.status === "failed" || raw.status === "error") {
    throw new PortalBackendError("The university portal did not complete this action. Check its status before trying again.");
  }
  const finalUrl = raw.final_url ?? raw.page_url ?? raw.course_url ?? null;
  return {
    status: typeof raw.status === "string" && raw.status ? raw.status : raw.success === true ? "success" : "unverified",
    message: typeof raw.message === "string" ? raw.message : null,
    finalUrl: typeof finalUrl === "string" ? finalUrl : null,
    raw,
  };
}

export interface AlmaRegistrationSupport {
  detail_url: string;
  title: string | null;
  number: string | null;
  supported: boolean;
  action: string | null;
  status: string | null;
  messages: string[];
  message: string | null;
}

export interface IliasWaitlistSupport {
  supported: boolean;
  requires_agreement: boolean;
  join_url: string | null;
  message: string | null;
}

export interface MoodleEnrolmentSupport {
  course_id: number | null;
  title: string;
  course_url: string | null;
  source_url: string;
  self_enrolment_available: boolean;
  requires_enrolment_key: boolean;
  enrolment_label: string | null;
}

export function loadAlmaRegistrationSupport(url: string): Promise<AlmaRegistrationSupport> {
  return fetchJson(`/api/alma/course-registration/support${queryString({ url })}`);
}

export function loadIliasWaitlistSupport(url: string): Promise<IliasWaitlistSupport> {
  return fetchJson(`/api/ilias/waitlist/support${queryString({ url })}`);
}

export function loadMoodleEnrolmentSupport(courseId: number): Promise<MoodleEnrolmentSupport> {
  return fetchJson(`/api/moodle/course/${courseId}/enrolment`);
}

export async function registerForAlmaCourse(url: string, planelementId?: string): Promise<CriticalActionResult> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/api/alma/course-registration${queryString({ url, planelement_id: planelementId })}`,
    { method: "POST" },
  );
  return actionResult(raw);
}

export async function addIliasFavorite(url: string): Promise<CriticalActionResult> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/api/ilias/favorites${queryString({ url })}`,
    { method: "POST" },
  );
  return actionResult(raw);
}

export async function joinIliasWaitlist(url: string, acceptAgreement: boolean): Promise<CriticalActionResult> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/api/ilias/waitlist/join${queryString({ url, accept_agreement: acceptAgreement })}`,
    { method: "POST" },
  );
  return actionResult(raw);
}

export async function enrolInMoodleCourse(courseId: number, enrolmentKey?: string): Promise<CriticalActionResult> {
  const body = new URLSearchParams();
  if (enrolmentKey) {
    body.set("enrolment_key", enrolmentKey);
  }
  const raw = await fetchJson<Record<string, unknown>>(`/api/moodle/course/${courseId}/enrol`, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body,
  });
  return actionResult(raw);
}

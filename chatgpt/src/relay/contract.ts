export interface RelayRequest { id: string; path: string; method: "GET" | "POST"; body?: string; contentType?: string; }
export interface RelayResponse { status: number; contentType: string; data: string; }
export const maxRelayBytes = 8 * 1024 * 1024;
export const maxJsonBytes = 1024 * 1024;
const reads = /^\/api\/(dashboard|course-detail|search|items\/[^/]+|mail\/(inbox|messages\/[^/]+)|campus\/canteens|ilias\/(tasks|memberships|search|content|forum|exercise|waitlist\/support)|alma\/(exams|timetable|enrollments|studyservice\/summary|documents\/current|study-planner|module-search(?:\/filters)?|course-search|module-detail|course-registration\/support)|moodle\/course\/\d+\/enrolment)$/;
const writes = /^\/api\/(alma\/course-registration|ilias\/(favorites|waitlist\/join)|moodle\/course\/\d+\/enrol)$/;
export function validateRelayRequest(request: Omit<RelayRequest, "id">) {
  const url = new URL(request.path, "http://localhost");
  if (!request.path.startsWith("/api/") || url.origin !== "http://localhost" || url.hash ||
      !(request.method === "GET" ? reads : writes).test(url.pathname) ||
      (request.body?.length ?? 0) > 16_384 ||
      (request.contentType !== undefined && request.contentType !== "application/x-www-form-urlencoded")) {
    throw new Error("Unsupported local study request.");
  }
  for (const key of ["url", "target"]) {
    const value = url.searchParams.get(key);
    if (!value?.includes(":")) continue;
    const target = new URL(value);
    if (target.protocol !== "https:" || target.username || target.password || target.port ||
        !["alma.uni-tuebingen.de", "ovidius.uni-tuebingen.de", "moodle.zdv.uni-tuebingen.de"].includes(target.hostname)) {
      throw new Error("Only official university resource URLs are supported.");
    }
  }
}

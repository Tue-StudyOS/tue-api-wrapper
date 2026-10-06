import { fetchPortalJson } from "./backend-http.js";
import { normalizeOptionalStudyTerm } from "./terms.js";
import type { UnifiedCourseDetail } from "./types/course.js";

export async function loadUnifiedCourseDetail({
  url = "",
  title = "",
  term = "",
  iliasLimit = 8,
}: {
  url?: string;
  title?: string;
  term?: string;
  iliasLimit?: number;
}): Promise<UnifiedCourseDetail> {
  const params = new URLSearchParams();
  if (url.trim()) {
    params.set("url", url.trim());
  }
  if (title.trim()) {
    params.set("title", title.trim());
  }
  const normalizedTerm = normalizeOptionalStudyTerm(term);
  if (normalizedTerm) {
    params.set("term", normalizedTerm);
  }
  params.set("ilias_limit", String(iliasLimit));
  return fetchPortalJson(`/api/course-detail?${params.toString()}`);
}

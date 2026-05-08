export function buildCareerHref(options: {
  query?: string;
  projectTypeId?: number | null;
  projectSubtypeId?: number | null;
  industryId?: number | null;
  postalCode?: string | null;
  projectId?: number | null;
  page?: number | null;
}) {
  const params = new URLSearchParams();
  if (options.query?.trim()) {
    params.set("query", options.query.trim());
  }
  if (options.projectTypeId) {
    params.set("projectTypeId", String(options.projectTypeId));
  }
  if (options.projectSubtypeId) {
    params.set("projectSubtypeId", String(options.projectSubtypeId));
  }
  if (options.industryId) {
    params.set("industryId", String(options.industryId));
  }
  if (options.postalCode?.trim()) {
    params.set("postalCode", options.postalCode.trim());
  }
  if (options.projectId) {
    params.set("projectId", String(options.projectId));
  }
  if (options.page && options.page > 1) {
    params.set("page", String(options.page));
  }
  const query = params.toString();
  return query ? `/career?${query}` : "/career";
}

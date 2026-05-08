import type { Route } from "next";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { buildCareerHref } from "./career-links";
import type {
  CareerProjectDetail,
  CareerSearchFilters,
  CareerSearchResponse
} from "../lib/product-types";

function formatDate(value: string | null) {
  if (!value) {
    return null;
  }
  return new Intl.DateTimeFormat("de-DE", { dateStyle: "medium" }).format(new Date(value));
}

export function CareerHub({
  search,
  filters,
  detail,
  query,
  selectedProjectTypeId,
  selectedProjectSubtypeId,
  selectedIndustryId,
  selectedPostalCode,
  currentPage
}: {
  search: CareerSearchResponse;
  filters: CareerSearchFilters;
  detail: CareerProjectDetail | null;
  query: string;
  selectedProjectTypeId: number | null;
  selectedProjectSubtypeId: number | null;
  selectedIndustryId: number | null;
  selectedPostalCode: string;
  currentPage: number;
}) {
  return (
    <>
      <Card className="border-primary/15 bg-primary/5">
        <CardHeader>
          <div>
            <CardDescription>praxisportal.uni-tuebingen.de</CardDescription>
            <CardTitle className="text-2xl">Career</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse public internships, thesis topics, jobs, and working-student roles through the live Praxisportal search index.
            </p>
          </div>
          <CardAction>
            <Button variant="outline" size="xs" asChild>
              <a href={search.source_url} target="_blank" rel="noreferrer">
                Open Praxisportal
              </a>
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          <form action="/career" method="get" className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_190px_190px_190px_190px_auto] lg:items-end">
            <div className="min-w-0">
              <label htmlFor="career-query" className="text-xs uppercase tracking-wide text-muted-foreground">
                Search
              </label>
              <Input id="career-query" name="query" defaultValue={query} placeholder="Cyber security, machine learning, biology…" />
            </div>
            <div>
              <label htmlFor="career-project-type" className="text-xs uppercase tracking-wide text-muted-foreground">
                Project type
              </label>
              <select
                id="career-project-type"
                name="projectTypeId"
                defaultValue={selectedProjectTypeId ? String(selectedProjectTypeId) : ""}
                className="h-9 w-full rounded-lg border border-input bg-input/50 px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
              >
                <option value="">Any</option>
                {filters.project_types.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="career-project-subtype" className="text-xs uppercase tracking-wide text-muted-foreground">
                Subtype
              </label>
              <select
                id="career-project-subtype"
                name="projectSubtypeId"
                defaultValue={selectedProjectSubtypeId ? String(selectedProjectSubtypeId) : ""}
                className="h-9 w-full rounded-lg border border-input bg-input/50 px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
              >
                <option value="">Any</option>
                {filters.project_subtypes.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="career-industry" className="text-xs uppercase tracking-wide text-muted-foreground">
                Industry
              </label>
              <select
                id="career-industry"
                name="industryId"
                defaultValue={selectedIndustryId ? String(selectedIndustryId) : ""}
                className="h-9 w-full rounded-lg border border-input bg-input/50 px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
              >
                <option value="">Any</option>
                {filters.industries.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="career-postal-code" className="text-xs uppercase tracking-wide text-muted-foreground">
                Town
              </label>
              <select
                id="career-postal-code"
                name="postalCode"
                defaultValue={selectedPostalCode}
                className="h-9 w-full rounded-lg border border-input bg-input/50 px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
              >
                <option value="">Any</option>
                {filters.postal_codes.map((option) => (
                  <option key={option.code} value={option.code}>{option.label}</option>
                ))}
              </select>
            </div>
            <Button type="submit">Apply</Button>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Open roles</CardTitle>
            <CardDescription>
              {search.total_hits} live hits across internships, theses, jobs, and working-student roles.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {search.items.map((item) => (
              <Link
                key={item.id}
                href={buildCareerHref({
                  query,
                  projectTypeId: selectedProjectTypeId,
                  projectSubtypeId: selectedProjectSubtypeId,
                  industryId: selectedIndustryId,
                  postalCode: selectedPostalCode,
                  projectId: item.id,
                  page: currentPage
                }) as Route}
                className="block rounded-lg border border-border p-4 transition-colors hover:bg-muted/40"
              >
                <div className="flex flex-wrap gap-2">
                  {item.project_types.map((projectType) => (
                    <Badge key={`${item.id}-${projectType}`} variant="secondary">{projectType}</Badge>
                  ))}
                  {item.location ? <Badge variant="outline">{item.location}</Badge> : null}
                </div>
                <p className="mt-3 text-sm font-medium">{item.title}</p>
                {item.organizations.length ? (
                  <p className="mt-1 text-xs text-muted-foreground">{item.organizations.join(" · ")}</p>
                ) : null}
                {item.preview ? (
                  <p className="mt-3 text-sm text-muted-foreground">{item.preview}</p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  {item.start_date ? <span>Start {formatDate(item.start_date)}</span> : null}
                  {item.created_at ? <span>Listed {formatDate(item.created_at)}</span> : null}
                </div>
              </Link>
            ))}

            {search.total_pages > 1 ? (
              <div className="flex items-center justify-between border-t border-border pt-3">
                <Button variant="outline" size="xs" asChild disabled={currentPage <= 1}>
                  <Link
                    href={buildCareerHref({
                      query,
                      projectTypeId: selectedProjectTypeId,
                      projectSubtypeId: selectedProjectSubtypeId,
                      industryId: selectedIndustryId,
                      postalCode: selectedPostalCode,
                      page: currentPage - 1
                    }) as Route}
                  >
                    Previous
                  </Link>
                </Button>
                <p className="text-xs text-muted-foreground">
                  Page {currentPage} of {Math.max(search.total_pages, 1)}
                </p>
                <Button variant="outline" size="xs" asChild disabled={currentPage >= search.total_pages}>
                  <Link
                    href={buildCareerHref({
                      query,
                      projectTypeId: selectedProjectTypeId,
                      projectSubtypeId: selectedProjectSubtypeId,
                      industryId: selectedIndustryId,
                      postalCode: selectedPostalCode,
                      page: currentPage + 1
                    }) as Route}
                  >
                    Next
                  </Link>
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{detail ? detail.title : "Select a role"}</CardTitle>
            <CardDescription>{detail?.location ?? "Choose a result to inspect its full description and requirements."}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {detail ? (
              <>
                <div className="flex flex-wrap gap-2">
                  {detail.project_types.map((projectType) => (
                    <Badge key={`${detail.id}-${projectType}`} variant="secondary">{projectType}</Badge>
                  ))}
                  {detail.industries.map((industry) => (
                    <Badge key={`${detail.id}-${industry}`} variant="outline">{industry}</Badge>
                  ))}
                </div>
                {detail.organizations.length ? (
                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Organizations</p>
                    {detail.organizations.map((organization) => (
                      <div key={`${detail.id}-${organization.name}`} className="rounded-2xl border border-border px-3 py-2">
                        <p className="text-sm font-medium">{organization.name}</p>
                        {organization.logo_url ? (
                          <a href={organization.logo_url} target="_blank" rel="noreferrer" className="text-xs text-primary">
                            Logo asset
                          </a>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
                {detail.description ? (
                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Description</p>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">{detail.description}</p>
                  </div>
                ) : null}
                {detail.requirements ? (
                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Requirements</p>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">{detail.requirements}</p>
                  </div>
                ) : null}
                {detail.source_url ? (
                  <Button variant="outline" asChild>
                    <a href={detail.source_url} target="_blank" rel="noreferrer">
                      Open original listing
                    </a>
                  </Button>
                ) : null}
              </>
            ) : (
              <div className="rounded-lg bg-muted px-4 py-5 text-sm text-muted-foreground">
                Role descriptions, requirements, and organization details appear here after you select a result.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

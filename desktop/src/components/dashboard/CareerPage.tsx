import type { useCareerSearch } from "../../lib/use-career-search";
import type { CareerFacetOption, CareerProjectDetail, CareerProjectSummary } from "../../lib/career-types";
import { EmptyState, PanelHeader } from "./DashboardPrimitives";
import type { DashboardPageProps } from "./types";

type CareerState = ReturnType<typeof useCareerSearch>;

export function CareerPage({ career, state }: DashboardPageProps & { career: CareerState }) {
  const response = career.response;
  const items = response?.items ?? [];
  if (career.selectedId) {
    return (
      <CareerDetailPage
        detail={career.detail}
        detailLoading={career.detailLoading}
        error={career.error}
        onBack={career.clearSelection}
      />
    );
  }

  return (
    <section className="career-layout">
      <article className="panel career-search-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Praxisportal</p>
            <h3>Career</h3>
          </div>
          <span>{response ? `${response.total_hits} live` : "Public listings"}</span>
        </div>
        <div className="career-filter-grid">
          <label className="field">
            <span>Search</span>
            <input
              className="search-input"
              onChange={(event) => career.setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && void career.refresh(0)}
              placeholder="Internship, thesis, working student"
              value={career.query}
            />
          </label>
          <CareerSelect
            label="Project type"
            onChange={(value) => career.setProjectTypeId(value)}
            options={career.filters?.project_types ?? response?.filters.project_types ?? []}
            value={career.projectTypeId}
          />
          <CareerSelect
            label="Industry"
            onChange={(value) => career.setIndustryId(value)}
            options={career.filters?.industries ?? response?.filters.industries ?? []}
            value={career.industryId}
          />
          <button className="primary-button" disabled={!state.backendUrl || career.loading} onClick={() => void career.refresh(0)} type="button">
            {career.loading ? "Searching..." : "Search"}
          </button>
        </div>
        {career.error ? <p className="inline-error">{career.error}</p> : null}
      </article>

      <article className="panel career-result-panel">
        <PanelHeader title="Open roles" meta={response ? `${items.length} shown` : "Not loaded"} />
        <div className="career-result-list">
          {items.map((item) => (
            <CareerResultRow
              item={item}
              key={item.id}
              onSelect={() => void career.selectProject(item.id)}
            />
          ))}
          {response && !items.length ? <EmptyState>No Praxisportal listings matched the current filters.</EmptyState> : null}
          {!response && !career.loading ? <EmptyState>Search public Praxisportal listings for internships, theses, jobs, and working-student roles.</EmptyState> : null}
        </div>
        {response && response.total_pages > 1 ? (
          <div className="career-pagination">
            <button className="secondary-button compact-button" disabled={response.page <= 0 || career.loading} onClick={() => void career.refresh(response.page - 1)} type="button">
              Previous
            </button>
            <span>{response.page + 1} / {response.total_pages}</span>
            <button className="secondary-button compact-button" disabled={response.page + 1 >= response.total_pages || career.loading} onClick={() => void career.refresh(response.page + 1)} type="button">
              Next
            </button>
          </div>
        ) : null}
      </article>

    </section>
  );
}

function CareerSelect({
  label,
  onChange,
  options,
  value
}: {
  label: string;
  onChange: (value: number | null) => void;
  options: CareerFacetOption[];
  value: number | null;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select className="career-select" onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)} value={value ?? ""}>
        <option value="">Any</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>{option.label} ({option.count})</option>
        ))}
      </select>
    </label>
  );
}

function CareerResultRow({ item, onSelect }: { item: CareerProjectSummary; onSelect: () => void }) {
  return (
    <button className="career-result-row" onClick={onSelect} type="button">
      <div className="career-tag-list">
        {item.project_types.slice(0, 2).map((projectType) => <span key={projectType}>{projectType}</span>)}
        {item.location ? <span>{item.location}</span> : null}
      </div>
      <strong>{item.title}</strong>
      {item.organizations.length ? <small>{item.organizations.join(" · ")}</small> : null}
      {item.preview ? <p>{item.preview}</p> : null}
      <small>{[dateLabel("Start", item.start_date), dateLabel("Listed", item.created_at)].filter(Boolean).join(" · ")}</small>
    </button>
  );
}

function CareerDetailPage({
  detail,
  detailLoading,
  error,
  onBack
}: {
  detail: CareerProjectDetail | null;
  detailLoading: boolean;
  error: string | null;
  onBack: () => void;
}) {
  return (
    <section className="panel career-detail-page">
      <div className="course-detail-toolbar">
        <button className="ghost-button compact-button" onClick={onBack} type="button">Back</button>
        <span>{detailLoading ? "Loading listing" : detail?.location ?? "Praxisportal"}</span>
      </div>
      {error ? <p className="inline-error">{error}</p> : null}
      {detail ? (
        <>
          <div className="career-detail-heading">
            <p className="eyebrow">Praxisportal listing</p>
            <h2>{detail.title}</h2>
            {detail.location ? <p className="muted">{detail.location}</p> : null}
          </div>
          <CareerDetail detail={detail} />
        </>
      ) : null}
      {!detail && detailLoading ? <EmptyState>Loading Praxisportal listing...</EmptyState> : null}
      {!detail && !detailLoading ? <EmptyState>The listing detail could not be loaded.</EmptyState> : null}
    </section>
  );
}

function CareerDetail({ detail }: { detail: CareerProjectDetail }) {
  return (
    <div className="detail-section-list">
      <div className="career-tag-list">
        {[...detail.project_types, ...detail.industries].map((tag) => <span key={tag}>{tag}</span>)}
      </div>
      {detail.organizations.length ? (
        <section className="detail-section-list">
          <h4>Organizations</h4>
          {detail.organizations.map((organization) => (
            <div className="detail-line" key={`${detail.id}-${organization.name}`}>
              <span>Organization</span>
              <strong>{organization.name}</strong>
            </div>
          ))}
        </section>
      ) : null}
      <CareerTextBlock title="Description" value={detail.description} />
      <CareerTextBlock title="Requirements" value={detail.requirements} />
      {detail.source_url ? (
        <button className="secondary-button" onClick={() => void window.desktop.openExternal(detail.source_url ?? "")} type="button">
          Open original listing
        </button>
      ) : null}
    </div>
  );
}

function CareerTextBlock({ title, value }: { title: string; value: string | null }) {
  if (!value?.trim()) return null;
  return (
    <section>
      <h4>{title}</h4>
      <p className="career-detail-text">{value}</p>
    </section>
  );
}

function dateLabel(label: string, value: string | null): string | null {
  if (!value) return null;
  return `${label} ${new Intl.DateTimeFormat("de-DE", { dateStyle: "medium" }).format(new Date(value))}`;
}

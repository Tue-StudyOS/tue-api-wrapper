import type { CourseDiscoveryResult } from "../../lib/course-discovery-types";
import { DiscoveryFilterCombobox } from "./DiscoveryFilterCombobox";
import type { CourseDiscoveryPageProps } from "./types";

const SOURCE_OPTIONS = [
  { id: "alma", label: "Alma courses and modules" },
  { id: "ilias", label: "ILIAS" },
  { id: "moodle", label: "Moodle" }
];

export function CourseDiscoveryPage({
  discovery,
  discoveryError,
  discoveryLoading,
  discoverySyncing,
  onOpenCourseDetail,
  onSearchDiscovery,
  onSyncDiscovery,
  setDiscoveryDegrees,
  setDiscoveryIncludePrivate,
  setDiscoveryModuleCodes,
  setDiscoveryQuery,
  setDiscoverySources
}: CourseDiscoveryPageProps) {
  const results = discovery.response?.results ?? [];
  const status = discovery.status ?? discovery.response?.status;

  return (
    <div className="course-discovery-layout">
      <section className="panel course-discovery-search">
        <div className="section-heading">
          <h3>Course discovery</h3>
          <span>{status ? `${status.document_count} indexed` : "Not synced"}</span>
        </div>
        <div className="field">
          <span>Search</span>
          <input
            className="search-input"
            onChange={(event) => setDiscoveryQuery(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" ? void onSearchDiscovery() : undefined}
            placeholder="Course, module, topic, lecturer"
            value={discovery.query}
          />
        </div>
        <div className="source-toggle-list">
          {SOURCE_OPTIONS.map((source) => (
            <label key={source.id} className="check-row">
              <input
                checked={discovery.sources.includes(source.id)}
                onChange={() => setDiscoverySources(toggle(discovery.sources, source.id))}
                type="checkbox"
              />
              <span>{source.label}</span>
            </label>
          ))}
        </div>
        <div className="discovery-filter-grid">
          <DiscoveryFilterCombobox
            label="Module area or code"
            onChange={setDiscoveryModuleCodes}
            options={status?.facets.module_codes ?? []}
            placeholder="All areas and codes"
            values={discovery.moduleCodes}
          />
          <DiscoveryFilterCombobox
            label="Study program"
            onChange={setDiscoveryDegrees}
            options={status?.facets.degrees ?? []}
            placeholder="All programs"
            values={discovery.degrees}
          />
        </div>
        <label className="check-row">
          <input
            checked={discovery.includePrivate}
            onChange={(event) => setDiscoveryIncludePrivate(event.target.checked)}
            type="checkbox"
          />
          <span>Include authenticated local sources</span>
        </label>
        <button
          className="primary-button full-width"
          disabled={discoveryLoading || !discovery.query.trim()}
          onClick={() => void onSearchDiscovery()}
          type="button"
        >
          {discoveryLoading ? "Searching..." : "Search courses"}
        </button>
        <button
          className="secondary-button full-width"
          disabled={discoverySyncing}
          onClick={() => void onSyncDiscovery()}
          type="button"
        >
          {discoverySyncing ? "Syncing..." : "Sync course index"}
        </button>
        {status ? (
          <p className="form-note">
            {status.semantic_available
              ? `Semantic search via ${status.vector_store} and ${status.embedding_model}. ${syncLabel(status.last_refresh)}`
              : `Cached lexical search. ${syncLabel(status.last_refresh)}`}
          </p>
        ) : null}
        {discoveryError ? <p className="inline-error">{discoveryError}</p> : null}
        {discovery.response?.errors.map((error) => <p key={error} className="inline-error">{error}</p>)}
      </section>

      <section className="panel course-discovery-results">
        <div className="section-heading">
          <h3>Results</h3>
          <span>{results.length} matches</span>
        </div>
        <div className="discovery-result-list">
          {results.map((result) => (
            <DiscoveryResultRow key={result.document.id} onOpenCourseDetail={onOpenCourseDetail} result={result} />
          ))}
          {!results.length ? (
            <p className="muted">Sync the course index, then search across Alma, ILIAS, and Moodle.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function DiscoveryResultRow({
  onOpenCourseDetail,
  result
}: {
  onOpenCourseDetail: CourseDiscoveryPageProps["onOpenCourseDetail"];
  result: CourseDiscoveryResult;
}) {
  const document = result.document;
  return (
    <button
      className="discovery-result-row"
      onClick={() => onOpenCourseDetail({
        title: document.module_code || document.title,
        url: almaDetailUrl(document.url),
        term: document.term,
        sourceLabel: `Discovery · ${document.source}`
      })}
      type="button"
    >
      <div>
        <span className="source-pill">{discoverySourceLabel(document.source, document.kind)}</span>
        <strong>{document.title}</strong>
        <span>{document.text}</span>
      </div>
      <div className="result-meta">
        <span>{document.module_categories[0] || document.module_code || document.term || result.match_reason}</span>
        <strong>{result.score.toFixed(1)}</strong>
      </div>
    </button>
  );
}

function discoverySourceLabel(source: string, kind: string): string {
  if (source === "alma" && kind === "module") return "Alma module handbook";
  if (source === "alma" && kind === "course") return "Alma course search";
  if (source === "alma" && kind === "lecture") return "Alma current lectures";
  return `${source} / ${kind}`;
}

function almaDetailUrl(url: string | null): string | null {
  return url && /\/alma\//i.test(url) ? url : null;
}

function toggle(values: string[], value: string): string[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function syncLabel(value: string | null): string {
  return value ? `Last synced ${new Date(value).toLocaleString()}.` : "Sync the index to search the cached corpus.";
}

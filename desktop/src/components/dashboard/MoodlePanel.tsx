import type { MoodleSnapshot } from "../../lib/moodle-types";
import { EmptyState, PanelHeader } from "./DashboardPrimitives";

export function MoodlePanel({
  data,
  error,
  loading,
  onRefresh
}: {
  data: MoodleSnapshot | null;
  error: string | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  return (
    <article className="panel wide-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Moodle</p>
          <h3>Courses, calendar, and updates</h3>
        </div>
        <button className="ghost-button compact-button" disabled={loading} onClick={onRefresh} type="button">
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>
      {error ? <p className="inline-error">{error}</p> : null}
      {data?.errors.map((item) => <p key={item} className="inline-error">{item}</p>)}
      <div className="moodle-grid">
        <MoodleList
          title="Upcoming"
          meta={`${data?.dashboard?.events.length ?? 0} events`}
          items={(data?.dashboard?.events ?? []).slice(0, 5).map((event) => ({
            title: event.title,
            detail: [event.course_name, event.formatted_time].filter(Boolean).join(" · ") || "Moodle event",
            url: event.action_url
          }))}
        />
        <MoodleList
          title="Courses"
          meta={`${data?.dashboard?.courses.length ?? 0} enrolled`}
          items={(data?.dashboard?.courses ?? []).slice(0, 5).map((course) => ({
            title: course.title,
            detail: [course.shortname, course.category_name].filter(Boolean).join(" · ") || "Moodle course",
            url: course.url
          }))}
        />
        <MoodleList
          title="Grades"
          meta={`${data?.grades?.items.length ?? 0} rows`}
          items={(data?.grades?.items ?? []).slice(0, 5).map((grade) => ({
            title: grade.course_title,
            detail: [grade.grade, grade.percentage, grade.range_hint].filter(Boolean).join(" · ") || "No grade label",
            url: grade.url
          }))}
        />
        <MoodleList
          title="Messages"
          meta={`${(data?.messages?.items.length ?? 0) + (data?.notifications?.items.length ?? 0)} updates`}
          items={[
            ...(data?.messages?.items ?? []).slice(0, 3).map((message) => ({
              title: message.title,
              detail: [message.sender, message.preview].filter(Boolean).join(" · ") || "Moodle message",
              url: message.url
            })),
            ...(data?.notifications?.items ?? []).slice(0, 2).map((notification) => ({
              title: notification.title,
              detail: notification.body || "Moodle notification",
              url: notification.url
            }))
          ]}
        />
      </div>
      {!data && !loading ? <EmptyState>Moodle data has not been loaded yet.</EmptyState> : null}
    </article>
  );
}

function MoodleList({
  items,
  meta,
  title
}: {
  items: Array<{ title: string; detail: string; url: string | null }>;
  meta: string;
  title: string;
}) {
  return (
    <section className="moodle-card">
      <PanelHeader title={title} meta={meta} />
      <div className="stack-list">
        {items.map((item) => (
          <button
            className="link-row compact-row"
            disabled={!item.url}
            key={`${title}-${item.title}-${item.url}`}
            onClick={() => item.url ? void window.desktop.openExternal(item.url) : undefined}
            type="button"
          >
            <div>
              <strong>{item.title}</strong>
              <span>{item.detail}</span>
            </div>
            <span className="row-action-label">{item.url ? "Open" : "View"}</span>
          </button>
        ))}
        {!items.length ? <EmptyState>No {title.toLowerCase()} returned.</EmptyState> : null}
      </div>
    </section>
  );
}

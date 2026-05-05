import type { useMoodleSnapshot } from "../../lib/use-moodle-snapshot";
import { EmptyState, PanelHeader } from "./DashboardPrimitives";
import { MoodlePanel } from "./MoodlePanel";
import type { DashboardPageProps } from "./types";

export function LearningPage({ data, moodle }: DashboardPageProps & { moodle: ReturnType<typeof useMoodleSnapshot> }) {
  return (
    <div className="content-grid">
      <article className="panel">
        <PanelHeader title="ILIAS tasks" meta={`${data?.ilias.tasks.length ?? 0} visible`} />
        <div className="stack-list">
          {(data?.ilias.tasks ?? []).map((task) => (
            <button key={`${task.title}-${task.url}`} className="link-row" onClick={() => void window.desktop.openExternal(task.url)}>
              <div>
                <strong>{task.title}</strong>
                <span>{task.item_type || "ILIAS item"}</span>
              </div>
              <span className="row-action-label">{task.end ? `Due ${task.end}` : "Open"}</span>
            </button>
          ))}
          {data?.ilias.tasks.length === 0 ? <EmptyState>No ILIAS tasks returned by the backend.</EmptyState> : null}
        </div>
      </article>

      <article className="panel">
        <PanelHeader title="Learning spaces" meta={`${data?.ilias.memberships.length ?? 0} visible`} />
        <div className="stack-list">
          {(data?.ilias.memberships ?? []).map((space) => (
            <button key={`${space.title}-${space.url}`} className="link-row" onClick={() => void window.desktop.openExternal(space.url)}>
              <div>
                <strong>{space.title}</strong>
                <span>{space.description || space.properties[0] || "Open learning space"}</span>
              </div>
              <span className="row-action-label">{space.kind || "Space"}</span>
            </button>
          ))}
          {data?.ilias.memberships.length === 0 ? <EmptyState>No learning spaces returned by ILIAS.</EmptyState> : null}
        </div>
      </article>

      <MoodlePanel
        data={moodle.data}
        error={moodle.error}
        loading={moodle.loading}
        onRefresh={() => void moodle.refresh()}
      />
    </div>
  );
}

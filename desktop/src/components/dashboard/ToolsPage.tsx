import { useState } from "react";

import type { DiscoverySettings } from "../../../shared/desktop-types";
import { refreshCourseDiscoveryIndex } from "../../lib/api";
import { FeedbackPanel } from "./FeedbackPanel";
import { PeopleSearchPanel } from "./PeopleSearchPanel";
import { PanelHeader } from "./DashboardPrimitives";
import { TimmsArchivePanel } from "./TimmsArchivePanel";
import type { DashboardPageProps } from "./types";

type ToolTab = "timms" | "people" | "feedback" | "settings";

export function ToolsPage({
  data,
  loading,
  onClearCredentials,
  onRefresh,
  onRestart,
  state
}: DashboardPageProps & {
  loading: boolean;
  onClearCredentials: () => Promise<void>;
  onRefresh: () => void;
  onRestart: () => Promise<void>;
}) {
  const [tab, setTab] = useState<ToolTab>("timms");
  const links = state.backendUrl
    ? [
      { label: "Backend API docs", url: `${state.backendUrl}/docs`, detail: "OpenAPI reference" },
      { label: "Dashboard JSON", url: `${state.backendUrl}/api/dashboard`, detail: "Current desktop payload" },
      { label: "Moodle grades", url: `${state.backendUrl}/api/moodle/grades`, detail: "Grades endpoint" },
      { label: "Campus buildings", url: `${state.backendUrl}/api/campus/buildings`, detail: "Campus directory" }
    ]
    : [];

  if (state.backendUrl && data?.documents.currentDownloadUrl) {
    links.push({
      label: "Current Alma PDF",
      url: `${state.backendUrl}${data.documents.currentDownloadUrl}`,
      detail: "Latest official document"
    });
  }

  const toolTabs = [
    ["timms", "TIMMS"],
    ["people", "People"],
    ["feedback", "Feedback"],
    ["settings", "Settings"]
  ] as const;

  return (
    <div className="tools-page">
      <section className="panel section-hero">
        <div>
          <p className="eyebrow">Discover</p>
          <h2>Archive, people, and app settings</h2>
          <p className="muted">TIMMS videos, university people search, and local app controls in one place.</p>
        </div>
        <div className="segmented-control">
          {toolTabs.map(([id, label]) => (
            <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)} type="button">
              {label}
            </button>
          ))}
        </div>
      </section>

      {tab === "timms" ? <TimmsArchivePanel baseUrl={state.backendUrl ?? null} /> : null}
      {tab === "people" ? <PeopleSearchPanel baseUrl={state.backendUrl ?? null} /> : null}
      {tab === "feedback" ? <FeedbackPanel /> : null}
      {tab === "settings" ? (
        <RuntimeSettings
          links={links}
          loading={loading}
          onClearCredentials={onClearCredentials}
          onRefresh={onRefresh}
          onRestart={onRestart}
          reportCount={data?.documents.reports.length ?? 0}
          reports={data?.documents.reports ?? []}
          state={state}
          stateReady={Boolean(state.backendUrl)}
        />
      ) : null}
    </div>
  );
}

function RuntimeSettings({
  links,
  loading,
  onClearCredentials,
  onRefresh,
  onRestart,
  reportCount,
  reports,
  state,
  stateReady
}: {
  links: { label: string; url: string; detail: string }[];
  loading: boolean;
  onClearCredentials: () => Promise<void>;
  onRefresh: () => void;
  onRestart: () => Promise<void>;
  reportCount: number;
  reports: { label: string; trigger_name: string }[];
  state: DashboardPageProps["state"];
  stateReady: boolean;
}) {
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [indexSyncing, setIndexSyncing] = useState(false);

  async function saveDiscoverySettings(nextSettings: DiscoverySettings): Promise<void> {
    setSettingsSaving(true);
    try {
      await window.desktop.saveDiscoverySettings(nextSettings);
    } finally {
      setSettingsSaving(false);
    }
  }

  async function syncCourseIndex(): Promise<void> {
    if (!state.backendUrl) {
      return;
    }
    setIndexSyncing(true);
    try {
      await refreshCourseDiscoveryIndex(state.backendUrl, { includePrivate: true });
    } catch (error) {
      console.error(error);
    } finally {
      setIndexSyncing(false);
    }
  }

  return (
    <div className="content-grid">
      <article className="panel">
        <PanelHeader title="App settings" meta={stateReady ? "Connected" : "Unavailable"} />
        <div className="stack-list">
          <div className="stack-row compact-row">
            <div>
              <strong>Account</strong>
              <span>{state.username ? state.username : "No account stored"}</span>
            </div>
          </div>
          <div className="stack-row compact-row">
            <div>
              <strong>Local service</strong>
              <span>{runtimeLabel(state.backendState, state.backendUrl, state.backendError)}</span>
            </div>
          </div>
          <div className="stack-row compact-row">
            <div>
              <strong>Feedback issue creation</strong>
              <span>Client-side GitHub issue drafts.</span>
            </div>
          </div>
          <div className="stack-row compact-row">
            <div>
              <strong>Semantic course search</strong>
              <span>{semanticLabel(state.discoverySettings.semanticSearchEnabled, settingsSaving)}</span>
            </div>
            <label className="switch-control">
              <input
                checked={state.discoverySettings.semanticSearchEnabled}
                disabled={settingsSaving}
                onChange={(event) => void saveDiscoverySettings({
                  ...state.discoverySettings,
                  semanticSearchEnabled: event.target.checked,
                  vectorStore: event.target.checked ? "lancedb" : "memory"
                })}
                type="checkbox"
              />
              <span />
            </label>
          </div>
          <label className="field">
            <span>Embedding model</span>
            <input
              key={state.discoverySettings.embeddingModel}
              disabled={settingsSaving || !state.discoverySettings.semanticSearchEnabled}
              onBlur={(event) => {
                const embeddingModel = event.target.value.trim();
                if (embeddingModel && embeddingModel !== state.discoverySettings.embeddingModel) {
                  void saveDiscoverySettings({ ...state.discoverySettings, embeddingModel });
                }
              }}
              placeholder="sentence-transformers/all-MiniLM-L6-v2"
              type="text"
              defaultValue={state.discoverySettings.embeddingModel}
            />
          </label>
          <div className="stack-row compact-row">
            <div>
              <strong>Course index</strong>
              <span>Sync Alma, ILIAS, and Moodle into the local discovery cache.</span>
            </div>
            <button
              className="secondary-button compact-button"
              disabled={!state.backendUrl || indexSyncing}
              onClick={() => void syncCourseIndex()}
              type="button"
            >
              {indexSyncing ? "Syncing..." : "Sync"}
            </button>
          </div>
        </div>
        <div className="settings-actions">
          <button className="secondary-button" disabled={loading || !state.backendUrl} onClick={onRefresh} type="button">
            {loading ? "Refreshing..." : "Refresh data"}
          </button>
          <button className="secondary-button" onClick={() => void onRestart()} type="button">
            Reconnect local service
          </button>
          <button className="ghost-button" onClick={() => void onClearCredentials()} type="button">
            Sign out
          </button>
        </div>
      </article>

      <article className="panel">
        <PanelHeader title="Developer links" meta={stateReady ? "Local API" : "Unavailable"} />
        <div className="stack-list">
          {links.map((link) => (
            <button key={link.url} className="link-row" onClick={() => void window.desktop.openExternal(link.url)} type="button">
              <div>
                <strong>{link.label}</strong>
                <span>{link.detail}</span>
              </div>
              <span>Open</span>
            </button>
          ))}
        </div>
      </article>

      <article className="panel">
        <PanelHeader title="Report jobs" meta={`${reportCount} available`} />
        <div className="stack-list">
          {reports.map((report) => (
            <div key={report.trigger_name} className="stack-row compact-row">
              <div>
                <strong>{report.label}</strong>
                <span>{report.trigger_name}</span>
              </div>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}


function semanticLabel(enabled: boolean, saving: boolean): string {
  if (saving) {
    return "Saving and restarting local service";
  }
  return enabled ? "Enabled with local LanceDB embeddings" : "Disabled";
}

function runtimeLabel(state: string, backendUrl: string | null, error: string | null): string {
  if (error) {
    return error;
  }
  if (state === "ready" && backendUrl) {
    return "Ready for local study data";
  }
  if (state === "starting") {
    return "Starting";
  }
  return "Not connected";
}

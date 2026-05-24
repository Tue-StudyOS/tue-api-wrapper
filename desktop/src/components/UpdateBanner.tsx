import type { DesktopUpdateState } from "../../shared/desktop-types";

export function UpdateBanner({
  state,
  onCheck,
  onInstall,
  onOpenReleases
}: {
  state: DesktopUpdateState | null;
  onCheck: () => Promise<void>;
  onInstall: () => Promise<void>;
  onOpenReleases: () => Promise<void>;
}) {
  if (!state || state.status === "unsupported" || state.status === "idle" || state.status === "not_available") {
    return null;
  }

  const action = state.canInstall ? (
    <button className="primary-button compact-button" onClick={() => void onInstall()} type="button">
      Restart to update
    </button>
  ) : state.status === "error" ? (
    <button className="secondary-button compact-button" onClick={() => void onCheck()} type="button">
      Try again
    </button>
  ) : (
    <button className="secondary-button compact-button" disabled type="button">
      {state.status === "checking" ? "Checking..." : "Downloading..."}
    </button>
  );

  return (
    <section className={`update-banner update-${state.status}`}>
      <div>
        <p className="eyebrow">Desktop update</p>
        <h2>{updateTitle(state)}</h2>
        <p className="muted">{updateDetail(state)}</p>
      </div>
      <div className="header-actions">
        {action}
        <button className="ghost-button compact-button" onClick={() => void onOpenReleases()} type="button">
          Releases
        </button>
      </div>
    </section>
  );
}

function updateTitle(state: DesktopUpdateState): string {
  if (state.status === "downloaded") {
    return `Version ${state.availableVersion ?? "update"} is ready`;
  }

  if (state.status === "error") {
    return "Update check failed";
  }

  if (state.status === "checking") {
    return "Checking for updates";
  }

  return `Downloading version ${state.availableVersion ?? "update"}`;
}

function updateDetail(state: DesktopUpdateState): string {
  if (state.status === "downloaded") {
    return "The update has been downloaded in the background and will install after restart.";
  }

  if (state.status === "error") {
    return state.error ?? "Could not check GitHub Releases for a newer desktop build.";
  }

  if (state.progressPercent !== null) {
    return `${Math.round(state.progressPercent)}% downloaded. You can keep using the app.`;
  }

  return "The app checks GitHub Releases and downloads newer desktop builds automatically.";
}

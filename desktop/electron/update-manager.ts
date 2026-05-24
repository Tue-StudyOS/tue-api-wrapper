import { app, Notification } from "electron";
import { EventEmitter } from "node:events";
import { autoUpdater } from "electron-updater";
import type { ProgressInfo, UpdateInfo } from "electron-updater";

import type { DesktopUpdateState, DesktopUpdateStatus } from "../shared/desktop-types";

const RELEASE_URL = "https://github.com/SebastianBoehler/tue-api-wrapper/releases";
const CHECK_INTERVAL_MS = 4 * 60 * 60 * 1000;

export class UpdateManager extends EventEmitter {
  private state: DesktopUpdateState = this.createInitialState();
  private interval: NodeJS.Timeout | null = null;
  private started = false;

  start(): void {
    if (this.started) {
      return;
    }

    this.started = true;
    this.configureUpdater();
    this.registerEvents();

    if (!this.state.isUpdateSupported) {
      this.emitState();
      return;
    }

    setTimeout(() => void this.checkForUpdates(), 5_000);
    this.interval = setInterval(() => void this.checkForUpdates(), CHECK_INTERVAL_MS);
  }

  getState(): DesktopUpdateState {
    return this.state;
  }

  async checkForUpdates(): Promise<DesktopUpdateState> {
    if (!this.state.isUpdateSupported) {
      return this.state;
    }

    if (this.state.status === "checking" || this.state.status === "downloading" || this.state.status === "downloaded") {
      return this.state;
    }

    this.patchState({ status: "checking", error: null, checkedAt: new Date().toISOString() });

    try {
      await autoUpdater.checkForUpdates();
    } catch (error) {
      this.patchState({ status: "error", error: formatUpdateError(error) });
    }

    return this.state;
  }

  installUpdate(): DesktopUpdateState {
    if (!this.state.canInstall) {
      throw new Error("No downloaded update is ready to install.");
    }

    autoUpdater.quitAndInstall(false, true);
    return this.state;
  }

  dispose(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }

  private createInitialState(): DesktopUpdateState {
    const supported = app.isPackaged;

    return {
      status: supported ? "idle" : "unsupported",
      currentVersion: app.getVersion(),
      availableVersion: null,
      progressPercent: null,
      checkedAt: null,
      error: supported ? null : "Updates are only available in packaged desktop builds.",
      isUpdateSupported: supported,
      canInstall: false,
      releaseUrl: RELEASE_URL
    };
  }

  private configureUpdater(): void {
    autoUpdater.autoDownload = true;
    autoUpdater.autoInstallOnAppQuit = true;
    autoUpdater.allowPrerelease = false;
  }

  private registerEvents(): void {
    autoUpdater.on("checking-for-update", () => {
      this.patchState({ status: "checking", error: null, checkedAt: new Date().toISOString() });
    });

    autoUpdater.on("update-available", (info: UpdateInfo) => {
      this.patchState({
        status: "available",
        availableVersion: info.version,
        progressPercent: null,
        error: null,
        canInstall: false
      });
    });

    autoUpdater.on("update-not-available", (info: UpdateInfo) => {
      this.patchState({
        status: "not_available",
        availableVersion: info.version,
        progressPercent: null,
        error: null,
        canInstall: false
      });
    });

    autoUpdater.on("download-progress", (progress: ProgressInfo) => {
      this.patchState({
        status: "downloading",
        progressPercent: Math.max(0, Math.min(100, progress.percent)),
        error: null
      });
    });

    autoUpdater.on("update-downloaded", (info: UpdateInfo) => {
      this.patchState({
        status: "downloaded",
        availableVersion: info.version,
        progressPercent: 100,
        error: null,
        canInstall: true
      });
      this.showReadyNotification(info.version);
    });

    autoUpdater.on("error", (error: Error) => {
      this.patchState({ status: "error", error: formatUpdateError(error), canInstall: false });
    });
  }

  private showReadyNotification(version: string): void {
    if (!Notification.isSupported()) {
      return;
    }

    new Notification({
      title: "TUE Study Hub update ready",
      body: `Version ${version} has been downloaded. Restart the app to install it.`
    }).show();
  }

  private patchState(patch: Partial<DesktopUpdateState> & { status?: DesktopUpdateStatus }): void {
    this.state = { ...this.state, ...patch };
    this.emitState();
  }

  private emitState(): void {
    this.emit("state-changed", this.state);
  }
}

function formatUpdateError(error: unknown): string {
  return error instanceof Error ? error.message : "Could not check for desktop updates.";
}

import { app, BrowserWindow } from "electron";

import { AssistantStore } from "./assistant-store";
import { BackendManager } from "./backend-manager";
import { CredentialStore } from "./credential-store";
import { DiscoverySettingsStore } from "./discovery-settings-store";
import { registerIpc } from "./ipc";
import { UpdateManager } from "./update-manager";
import { createMainWindow } from "./window";

let mainWindow: BrowserWindow | null = null;
let backendManager: BackendManager | null = null;
let updateManager: UpdateManager | null = null;

async function bootstrap(): Promise<void> {
  await app.whenReady();

  const store = new CredentialStore(app.getPath("userData"));
  const assistantStore = new AssistantStore(app.getPath("userData"));
  const discoverySettingsStore = new DiscoverySettingsStore(app.getPath("userData"));
  backendManager = new BackendManager(store, discoverySettingsStore);
  updateManager = new UpdateManager();
  registerIpc(backendManager, assistantStore, updateManager);
  await backendManager.initialize();

  mainWindow = createMainWindow();
  mainWindow.webContents.once("did-finish-load", () => {
    mainWindow?.webContents.send("desktop:state-changed", backendManager?.getState());
    mainWindow?.webContents.send("desktop:update-state-changed", updateManager?.getState());
  });

  backendManager.on("state-changed", (state) => {
    mainWindow?.webContents.send("desktop:state-changed", state);
  });

  updateManager.on("state-changed", (state) => {
    mainWindow?.webContents.send("desktop:update-state-changed", state);
  });
  updateManager.start();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", async () => {
  updateManager?.dispose();
  await backendManager?.dispose();
});

void bootstrap();

import { app, ipcMain, shell } from "electron";
import os from "node:os";

import type { AssistantChatRequest, AssistantConfig, CredentialInput, DesktopAppInfo, DiscoverySettings } from "../shared/desktop-types";
import { AssistantService } from "./assistant-service";
import { AssistantStore } from "./assistant-store";
import { BackendManager } from "./backend-manager";

export function registerIpc(manager: BackendManager, assistantStore: AssistantStore): void {
  const assistant = new AssistantService(manager);
  ipcMain.handle("desktop:get-state", () => manager.getState());
  ipcMain.handle("desktop:get-app-info", (): DesktopAppInfo => ({
    appVersion: app.getVersion(),
    buildNumber: app.getVersion(),
    systemVersion: `${os.type()} ${os.release()}`.slice(0, 60),
    deviceModel: `${os.platform()}-${os.arch()}`.slice(0, 60)
  }));
  ipcMain.handle("desktop:save-credentials", (_event, input: CredentialInput) => manager.saveCredentials(input));
  ipcMain.handle("desktop:clear-credentials", () => manager.clearCredentials());
  ipcMain.handle("desktop:restart-backend", () => manager.restart());
  ipcMain.handle("desktop:save-discovery-settings", (_event, input: DiscoverySettings) => manager.saveDiscoverySettings(input));
  ipcMain.handle("desktop:open-external", (_event, url: string) => shell.openExternal(url));
  ipcMain.handle("assistant:get-config", () => assistantStore.load());
  ipcMain.handle("assistant:save-config", (_event, input: AssistantConfig) => assistantStore.save(input));
  ipcMain.handle("assistant:chat", (_event, input: AssistantChatRequest) => assistant.chat(input));
}

import { contextBridge, ipcRenderer } from "electron";

import type {
  AssistantChatRequest,
  AssistantChatResponse,
  AssistantConfig,
  CredentialInput,
  DesktopAppInfo,
  DesktopRuntimeState,
  DesktopUpdateState,
  DiscoverySettings
} from "../shared/desktop-types";

contextBridge.exposeInMainWorld("desktop", {
  getState: (): Promise<DesktopRuntimeState> => ipcRenderer.invoke("desktop:get-state"),
  getAppInfo: (): Promise<DesktopAppInfo> => ipcRenderer.invoke("desktop:get-app-info"),
  saveCredentials: (input: CredentialInput): Promise<void> => ipcRenderer.invoke("desktop:save-credentials", input),
  clearCredentials: (): Promise<void> => ipcRenderer.invoke("desktop:clear-credentials"),
  restartBackend: (): Promise<void> => ipcRenderer.invoke("desktop:restart-backend"),
  saveDiscoverySettings: (input: DiscoverySettings): Promise<DiscoverySettings> => ipcRenderer.invoke("desktop:save-discovery-settings", input),
  openExternal: (url: string): Promise<void> => ipcRenderer.invoke("desktop:open-external", url),
  getUpdateState: (): Promise<DesktopUpdateState> => ipcRenderer.invoke("desktop:get-update-state"),
  checkForUpdates: (): Promise<DesktopUpdateState> => ipcRenderer.invoke("desktop:check-for-updates"),
  installUpdate: (): Promise<DesktopUpdateState> => ipcRenderer.invoke("desktop:install-update"),
  getAssistantConfig: (): Promise<AssistantConfig> => ipcRenderer.invoke("assistant:get-config"),
  saveAssistantConfig: (input: AssistantConfig): Promise<AssistantConfig> => ipcRenderer.invoke("assistant:save-config", input),
  sendAssistantMessage: (input: AssistantChatRequest): Promise<AssistantChatResponse> => ipcRenderer.invoke("assistant:chat", input),
  onStateChanged: (listener: (state: DesktopRuntimeState) => void): (() => void) => {
    const wrapped = (_event: Electron.IpcRendererEvent, state: DesktopRuntimeState) => listener(state);
    ipcRenderer.on("desktop:state-changed", wrapped);
    return () => ipcRenderer.removeListener("desktop:state-changed", wrapped);
  },
  onUpdateStateChanged: (listener: (state: DesktopUpdateState) => void): (() => void) => {
    const wrapped = (_event: Electron.IpcRendererEvent, state: DesktopUpdateState) => listener(state);
    ipcRenderer.on("desktop:update-state-changed", wrapped);
    return () => ipcRenderer.removeListener("desktop:update-state-changed", wrapped);
  }
});

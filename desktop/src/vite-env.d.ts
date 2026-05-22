/// <reference types="vite/client" />

import type {
  AssistantChatRequest,
  AssistantChatResponse,
  AssistantConfig,
  CredentialInput,
  DesktopAppInfo,
  DesktopRuntimeState,
  DiscoverySettings
} from "../shared/desktop-types";

declare global {
  interface Window {
    desktop: {
      getState(): Promise<DesktopRuntimeState>;
      getAppInfo(): Promise<DesktopAppInfo>;
      saveCredentials(input: CredentialInput): Promise<void>;
      clearCredentials(): Promise<void>;
      restartBackend(): Promise<void>;
      saveDiscoverySettings(input: DiscoverySettings): Promise<DiscoverySettings>;
      openExternal(url: string): Promise<void>;
      getAssistantConfig(): Promise<AssistantConfig>;
      saveAssistantConfig(input: AssistantConfig): Promise<AssistantConfig>;
      sendAssistantMessage(input: AssistantChatRequest): Promise<AssistantChatResponse>;
      onStateChanged(listener: (state: DesktopRuntimeState) => void): () => void;
    };
  }
}

export {};

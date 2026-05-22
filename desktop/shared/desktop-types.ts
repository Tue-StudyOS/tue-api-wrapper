export type BackendLifecycleState = "missing_credentials" | "starting" | "ready" | "error" | "stopped";

export interface CredentialInput {
  username: string;
  password: string;
}

export interface DesktopRuntimeState {
  hasCredentials: boolean;
  username: string | null;
  backendState: BackendLifecycleState;
  backendUrl: string | null;
  backendError: string | null;
  discoverySettings: DiscoverySettings;
}

export interface DesktopAppInfo {
  appVersion: string;
  buildNumber: string;
  systemVersion: string;
  deviceModel: string;
}

export interface DiscoverySettings {
  semanticSearchEnabled: boolean;
  vectorStore: "memory" | "lancedb";
  embeddingModel: string;
}

export interface AssistantConfig {
  baseUrl: string;
  model: string;
  apiKey: string;
}

export interface AssistantChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantToolCard {
  name: string;
  title: string;
  summary: string;
  data: unknown;
}

export interface AssistantToolCallTrace {
  id: string;
  name: string;
  title: string;
  arguments: Record<string, unknown>;
  status: "success" | "error";
  summary: string;
}

export interface AssistantChatRequest {
  messages: AssistantChatMessage[];
  config: AssistantConfig;
}

export interface AssistantChatResponse {
  text: string;
  toolCards: AssistantToolCard[];
  toolCalls: AssistantToolCallTrace[];
}

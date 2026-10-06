import { AsyncLocalStorage } from "node:async_hooks";
import type { StateStore } from "./auth/state-store.js";
import type { SidecarRelay } from "./relay/relay.js";

export interface StudyContext { userId: string; store: StateStore; relay: SidecarRelay; origin: URL; }
export const studyContext = new AsyncLocalStorage<StudyContext>();

import { randomBytes, randomUUID } from "node:crypto";

import { PortalBackendError } from "../backend.js";
import type { CriticalActionPublicIntent, CriticalActionResult } from "../types/actions.js";
import { asStructured, toolErrorResponse } from "../tool-runtime.js";
import { StateStore, digest } from "../auth/state-store.js";
import { studyContext } from "../request-context.js";
import { executeAction, type ActionCommand } from "./action-command.js";

export interface StoredCriticalAction {
  intent: CriticalActionPublicIntent;
  token: string;
  command: ActionCommand;
  execute: (enrolmentKey?: string) => Promise<CriticalActionResult>;
}

const internalStore = new StateStore(":memory:");
function context() { return studyContext.getStore() ?? { store: internalStore, userId: "internal-development" }; }
interface PersistedAction { intent: CriticalActionPublicIntent; command: ActionCommand; }
const expiryMs = 10 * 60 * 1000;

export function actionAnnotations(destructiveHint: boolean) {
  return {
    readOnlyHint: false,
    destructiveHint,
    openWorldHint: false,
    idempotentHint: false,
  };
}

export function storeAction(
  data: Omit<CriticalActionPublicIntent, "id" | "preparedAt" | "expiresAt">,
  command: ActionCommand,
) {
  const { store, userId } = context();
  store.prune();
  const now = new Date();
  const intent: CriticalActionPublicIntent = {
    ...data,
    id: randomUUID(),
    preparedAt: now.toISOString(),
    expiresAt: new Date(now.getTime() + expiryMs).toISOString(),
  };
  const stored: StoredCriticalAction = {
    intent,
    token: randomBytes(24).toString("base64url"),
    command,
    execute: key => executeAction(command, key),
  };
  store.put("action", `${userId}:${intent.id}:${digest(stored.token)}`, { intent, command }, Date.parse(intent.expiresAt));
  return stored;
}

export function preparedResponse(stored: StoredCriticalAction) {
  return {
    structuredContent: asStructured({
      view: "critical-action",
      intent: stored.intent,
    }),
    content: [
      {
        type: "text" as const,
        text: `Showing a confirmation UI for ${stored.intent.actionLabel}. No upstream action has been submitted.`,
      },
    ],
    _meta: {
      intent: stored.intent,
      confirmationToken: stored.token,
    },
  };
}

export async function prepareTool(loader: () => Promise<StoredCriticalAction>) {
  try {
    return preparedResponse(await loader());
  } catch (error) {
    if (error instanceof PortalBackendError) {
      return toolErrorResponse(error);
    }
    return toolErrorResponse(new PortalBackendError("The action could not be prepared. Contact support."));
  }
}

export function consumePendingAction(intentId: string, confirmationToken: string): StoredCriticalAction {
  const { store, userId } = context();
  const stored = store.take<PersistedAction>("action", `${userId}:${intentId}:${digest(confirmationToken)}`);
  if (!stored) {
    throw new PortalBackendError("This confirmation is no longer valid. Prepare the action again.");
  }
  if (Date.parse(stored.intent.expiresAt) <= Date.now()) {
    throw new PortalBackendError("This confirmation expired. Prepare the action again.");
  }
  return { ...stored, token: confirmationToken, execute: key => executeAction(stored.command, key) };
}

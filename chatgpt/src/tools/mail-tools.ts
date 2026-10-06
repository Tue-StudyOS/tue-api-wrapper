import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { loadMailInbox, loadMailMessage } from "../backend.js";
import { asStructured, limitSchema, readOnlyAnnotations, runReadTool } from "../tool-runtime.js";

export function registerMailTools(server: McpServer) {
  registerAppTool(
    server,
    "get_mail_inbox",
    {
      outputSchema: outputSchemas.get_mail_inbox,
      title: "Get mail inbox",
      description:
        "Use this when the user wants to triage inbox messages, filter by sender, search mailbox text, or look at unread mail.",
      inputSchema: {
        mailbox: z.string().optional(),
        limit: limitSchema,
        query: z.string().optional(),
        sender: z.string().optional(),
        unreadOnly: z.boolean().optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ mailbox, limit, query, sender, unreadOnly }) =>
      runReadTool(async () => {
        const inbox = await loadMailInbox({
          mailbox,
          limit,
          query,
          sender,
          unreadOnly,
        });
        return {
          structuredContent: asStructured(inbox),
          content: [
            {
              type: "text" as const,
              text: `Loaded ${inbox.messages.length} messages from ${inbox.mailbox} with ${inbox.unread_count} unread.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_mail_message",
    {
      outputSchema: outputSchemas.get_mail_message,
      title: "Get mail message detail",
      description:
        "Use this when the user wants the full plaintext body and headers for a specific mail UID from the inbox response.",
      inputSchema: {
        uid: z.string().min(1),
        mailbox: z.string().optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ uid, mailbox }) =>
      runReadTool(async () => {
        const message = await loadMailMessage(uid, mailbox);
        return {
          structuredContent: asStructured(message),
          content: [
            {
              type: "text" as const,
              text: `Loaded mail message "${message.subject}" from ${message.mailbox}.`,
            },
          ],
        };
      }),
  );
}

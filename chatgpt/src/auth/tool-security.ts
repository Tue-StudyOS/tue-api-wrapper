import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { studyContext } from "../request-context.js";
import { z } from "zod";
export function installToolSecurity(server: McpServer) {
  // The SDK's registration type exposes MCP metadata; OpenAI also reads the
  // top-level securitySchemes extension on tools/list.
  const setHandler = server.server.setRequestHandler.bind(server.server);
  server.server.setRequestHandler = ((schema, handler) => setHandler(schema, async (request, extra) => {
    const result = await handler(request, extra);
    if (request.method !== "tools/list" || !("tools" in result) || !Array.isArray(result.tools)) return result;
    const tools = result.tools as Tool[];
    return { ...result, tools: tools.map(tool => ({ ...tool, securitySchemes: tool._meta?.securitySchemes })) };
  })) as McpServer["server"]["setRequestHandler"];
  const register = server.registerTool.bind(server);
  server.registerTool = ((name, config, handler) => register(name, {
    ...config, _meta: { ...config._meta, securitySchemes: [{ type: "oauth2", scopes: ["study"] }] },
  }, handler)) as McpServer["registerTool"];
  server.registerTool("get_connection_profile", {
    title: "Connected student profile", description: "Return the opaque account ID for this local sidecar connection.",
    inputSchema: {}, outputSchema: { id: z.string() },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true },
    _meta: { "openai/profile": true },
  }, async () => {
    const id = studyContext.getStore()?.userId;
    if (!id) return { isError: true, content: [{ type: "text", text: "Connect your local sidecar first." }] };
    return { structuredContent: { id }, content: [{ type: "text", text: JSON.stringify({ id }) }] };
  });
}

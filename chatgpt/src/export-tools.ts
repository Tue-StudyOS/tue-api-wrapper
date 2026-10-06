import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createAppServer } from "./study-server.js";
const server = createAppServer(), client = new Client({ name: "submission-export", version: "1" });
const [local, remote] = InMemoryTransport.createLinkedPair();
try {
  await server.connect(remote); await client.connect(local);
  const tools = await client.listTools(), resources = await client.listResources();
  console.log(JSON.stringify({ tools: tools.tools.map(tool => ({ ...tool, securitySchemes: tool._meta?.securitySchemes })), resources: resources.resources }, null, 2));
} finally { await client.close(); await server.close(); }

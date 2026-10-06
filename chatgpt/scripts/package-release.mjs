import { readFile, writeFile, mkdir, cp, rm } from "node:fs/promises";
import { resolve, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
export function releaseOrigin(value) {
  const url = new URL(value);
  if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash ||
      !/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(url.hostname) ||
      ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) || /(?:^|\.)(?:example\.(?:com|org|net)|invalid|test|local)$/.test(url.hostname)) throw new Error("Use the real production HTTPS origin, without paths or credentials.");
  return url.origin;
}
export async function packageRelease(value, destination) {
  const origin = releaseOrigin(value);
  const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
  const output = resolve(destination ?? join(root, "release"));
  if (output === root || output === resolve(root, "..")) throw new Error("Release output must be a separate directory.");
  const bundle = join(output, "plugin");
  await rm(bundle, { recursive: true, force: true }); await mkdir(bundle, { recursive: true });
  const plugin = JSON.parse(await readFile(join(root, "plugin.json"), "utf8"));
  const publisher = JSON.parse(await readFile(join(root, "publisher.json"), "utf8"));
  plugin.author = publisher;
  const openai = plugin.extensions["com.openai"];
  openai.interface.developerName = publisher.name;
  Object.assign(openai.interface, { websiteURL: origin, supportURL: `${origin}/support`, privacyPolicyURL: `${origin}/privacy`, termsOfServiceURL: `${origin}/terms` });
  plugin.homepage = origin;
  await writeFile(join(bundle, "plugin.json"), JSON.stringify(plugin, null, 2) + "\n");
  await writeFile(join(bundle, "mcp.json"), JSON.stringify({ $schema: "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json", mcpServers: { tuebingen: { type: "streamable-http", url: `${origin}/mcp` } } }, null, 2) + "\n");
  for (const folder of ["skills", "assets"]) await cp(join(root, folder), join(bundle, folder), { recursive: true });
  await cp(join(root, "..", "LICENSE"), join(bundle, "LICENSE"));
  const discovery = spawnSync(process.execPath, [join(root, "dist/export-tools.js")], { encoding: "utf8", maxBuffer: 4 * 1024 * 1024 });
  if (discovery.status !== 0) throw new Error("Build the server before packaging. Tool discovery failed.");
  const inventory = JSON.parse(discovery.stdout);
  if (inventory.tools.length !== 28 || inventory.tools.some(tool => !tool.outputSchema || !tool._meta?.securitySchemes)) throw new Error("Submission tool inventory is incomplete.");
  await writeFile(join(output, "tool-inventory.json"), JSON.stringify(inventory, null, 2) + "\n");
  for (const file of ["SUBMISSION.md", "DEPLOYMENT.md", "RELEASE_REVIEW.md", "CAPACITY.md"]) await cp(join(root, file), join(output, file));
  const zip = join(output, "tuebingen-study-hub.zip"); await rm(zip, { force: true });
  const packed = spawnSync("zip", ["-q", "-r", zip, "plugin.json", "mcp.json", "skills", "assets", "LICENSE"], { cwd: bundle });
  if (packed.status !== 0) throw new Error("ZIP creation failed. Install zip and run the command again.");
  return { zip, toolCount: inventory.tools.length };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (!process.argv[2]) throw new Error("Usage: npm run release:package -- https://PRODUCTION_HOST [output-directory]");
  console.log(JSON.stringify(await packageRelease(process.argv[2], process.argv[3])));
}
